import os
import json
import zipfile
import shapefile
import defusedxml.minidom as md
from kml2geojson import build_feature_collection as kml2json
from geomet import wkt
from io import BytesIO
import geopandas

# taken from asf's Discovery-WKTUtils
# Repo: https://github.com/asfadmin/Discovery-WKTUtils
# File: https://github.com/asfadmin/Discovery-WKTUtils/blob/devel/WKTUtils/FilesToWKT.py
class filesToWKT:
    # files = [ open(dir, 'rb'), open(dir2, 'rb'), open(dir3, 'rb') ]
    def __init__(self, files):
        self.files = files
        self.errors = []
        self.returned_dict = {}
        # If they pass only one, make that a list of one:
        if not isinstance(files, type([])):
            self.files = [self.files]
        # Have to group all shp types together:
        file_dict = {}
        for file in self.files:
            try:
                full_name = file.filename
            except AttributeError:
                full_name = file.name
            name = ".".join(full_name.split(".")[:-1])  # Everything before the last dot.
            ext = full_name.split(".")[-1:][0].lower()  # Everything after the last dot.
            ### First see if geopandas can handle it.
            try:
                geoshape: geopandas.GeoDataFrame = geopandas.read_file(file)
                # Turn from GeoDataFrame to  GeoSeries:
                geoshape = geoshape.geometry
                # Add it to the file list:
                self.add_file_to_dict(file_dict, name+".pandas", geoshape)
                continue
            # If anything goes wrong, try to go back to the old ways:
            except:
                file.seek(0) # Move read curser to 0, lets you read again
            if ext == "zip":
                # First check for a full shapefile set:
                with BytesIO(file.read()) as zip_f:
                    zip_obj = zipfile.ZipFile(zip_f)
                    parts = zip_obj.namelist()
                    for part_path in parts:
                        # If it's a dir, skip it. ('parts' still contains the files in that dir)
                        if part_path.endswith("/"):
                            continue
                        self.add_file_to_dict(file_dict, part_path, zip_obj.read(part_path))
            else:
                # Try to add whatever it is:
                self.add_file_to_dict(file_dict, full_name, file.read())

        # With everything organized in dict, start parsing them:
        wkt_list = []
        for key, val in file_dict.items():
            ext = key.split(".")[-1:][0].lower()
            # If it's a shp set. (Check first, because 'file.kml.shp' will be loaded, and
            #       the key will become 'file.kml'. The val is always a dict for shps tho):
            if isinstance(val, type({})):
                returned_wkt = parse_shapefile(val)
            elif ext == "pandas":
                # For this, val IS the geopandas object.
                # Check if you need to reporject the wkt. (Might be None):
                if val.crs and val.crs != "EPSG:4326":
                    val = val.to_crs("EPSG:4326")
                if len(val) == 0:
                    continue
                elif len(val) == 1:
                    returned_wkt = json_to_wkt(val[0].__geo_interface__)
                else:
                    tmp_list = [json_to_wkt(shape.__geo_interface__) for shape in val]
                    returned_wkt = "GEOMETRYCOLLECTION ({0})".format(",".join(tmp_list))
            # Check for each type now:
            elif ext == "geojson":
                returned_wkt = parse_geojson(val)
            elif ext == "kml":
                returned_wkt = parse_kml(val)
            else:
                # This *should* never get hit, but someone might add a new file-type in 'add_file_to_dict' w/out declaring it here.
                self.errors.append({"type": "STREAM_UNKNOWN", "report": "Ignoring file with unknown tag. File: '{0}'".format(os.path.basename(key))})
                continue
            # If the parse function returned a json error:
            if isinstance(returned_wkt, type({})) and "error" in returned_wkt:
                # Give the error a better error discription:
                returned_wkt["error"]["report"] += " (Cannot load file: '{0}')".format(os.path.basename(key))
                self.errors.append(returned_wkt["error"])
                continue
            else:
                wkt_list.append(returned_wkt)

        # Turn it into a single WKT:
        full_wkt = "GEOMETRYCOLLECTION({0})".format(",".join(wkt_list))

        # Bring it to json and back, to collaps any nested GEOMETRYCOLLECTIONS.
        # It'll be in a collection if and only if there are more than one shapes.
        full_wkt = json_to_wkt(wkt.loads(full_wkt))
        self.returned_dict = {"parsed wkt": full_wkt}


    def getWKT(self):
        # Only return the 'errors' key IF there are errors...
        if self.errors != []:
            self.returned_dict['errors'] = self.errors
        return self.returned_dict

    # Helper for organizing files into a dict, combining shps/shx, etc.
    def add_file_to_dict(self, file_dict, full_name, file_stream):
        ext = full_name.split(".")[-1:][0].lower()              # Everything after the last dot.
        file_name = ".".join(full_name.split(".")[:-1])         # Everything before the last dot.

        # SHP'S:
        if ext in ["shp", "shx", "dbf"]:
            # Save shps as {"filename": {"shp": data, "shx": data, "dbf": data}, "file_2.kml": kml_data}
            if file_name not in file_dict:
                file_dict[file_name] = {}
            file_dict[file_name][ext] = BytesIO(file_stream)
        elif ext in ["pandas"]:
            file_dict[full_name] = file_stream # Actually geopandas object for this one.
        # BASIC FILES:
        elif ext in ["kml", "geojson"]:
            file_dict[full_name] = BytesIO(file_stream)
        # Else they pass a zip again:
        elif ext in ["zip"]:
            self.errors.append({"type": "FILE_UNZIP", "report": "Cannot unzip double-compressed files. File: '{0}'.".format(os.path.basename(full_name))})
        else:
            self.errors.append({"type": "FILE_UNKNOWN", "report": "Ignoring file with unknown extension. File: '{0}'.".format(os.path.basename(full_name))})



# Takes any json, and returns a list of all {"type": x, "coordinates": y} objects
# found, ignoring anything else in the block
def recurse_find_geojson(json_input):
    # NOTE: geojson doesn't go through this anymore, with adding geopandas
    # parser. Instead, make this happen AFTER shapes are loaded/transformed
    # to geojson, to simplify EVERYTHING handed to us down.
    if isinstance(json_input, type({})):
        # If it's a dict, try to load the minimal required for a shape.
        # Then recurse on every object, just incase more are nested inside:
        try:
            new_shape = { "type": json_input["type"], "coordinates": json_input["coordinates"] }
            yield new_shape
        except KeyError:
            pass
        for key_value_pair in json_input.items():
            yield from recurse_find_geojson(key_value_pair[1])
    # If it's a list, just loop through it:
    elif isinstance(json_input, type([])):
        for item in json_input:
            yield from recurse_find_geojson(item)

# Takes a json, and returns a possibly-simplified wkt_str
# Used by both parse_geojson, and parse_kml
def json_to_wkt(geojson):
    geojson_list = []
    for new_shape in recurse_find_geojson(geojson):
        geojson_list.append(new_shape)

    if len(geojson_list) == 0:
        return {'error': {'type': 'VALUE', 'report': 'Could not find any shapes inside geojson.'}}
    elif len(geojson_list) == 1:
        wkt_json = geojson_list[0]
    else:
        wkt_json = { 'type': 'GeometryCollection', 'geometries': geojson_list }

    try:
        wkt_str = wkt.dumps(wkt_json)
    except (KeyError, ValueError) as e:
        return {'error': {'type': 'VALUE', 'report': 'Problem converting a shape to string: {0}'.format(str(e))}}
    return wkt_str


def parse_geojson(f):
    try:
        data = f.read()
        geojson = json.loads(data)
    except json.JSONDecodeError as e:
        return {'error': {'type': 'DECODE', 'report': 'Could not parse GeoJSON: {0}'.format(str(e))}}
    except KeyError as e:
        return {'error': {'type': 'KEY', 'report': 'Missing expected key: {0}'.format(str(e))}}
    except ValueError as e:
        return {'error': {'type': 'VALUE', 'report': 'Could not parse GeoJSON: {0}'.format(str(e))}}
    return json_to_wkt(geojson)


def parse_kml(f):
    try:
        kml_str = f.read()
        kml_root = md.parseString(kml_str, forbid_dtd=True)
        wkt_json = kml2json(kml_root)
    # All these BUT the type/value errors are for the md.parseString:
    # except (DefusedXmlException, DTDForbidden, EntitiesForbidden, ExternalReferenceForbidden, NotSupportedError, TypeError, ValueError) as e:
    except Exception as e:
        return {'error': {'type': 'VALUE', 'report': 'Could not parse kml: {0}'.format(str(e))}}
    return json_to_wkt(wkt_json)

def parse_shapefile(fileset):
    try:
        reader = shapefile.Reader(**fileset)
        shapes = [i.__geo_interface__ for i in reader.shapes()]
    # In the sourcecode, it looks like sometimes the reader throws "Exception":
    except Exception as e:
        return {'error': {'type': 'VALUE', 'report': 'Could not parse shp: {0}'.format(str(e))}}
    wkt_json = {'type':'GeometryCollection', 'geometries': shapes }
    wkt_str = json_to_wkt(wkt_json)
    return wkt_str
