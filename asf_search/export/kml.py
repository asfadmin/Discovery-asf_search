import inspect
from types import GeneratorType
from asf_search import ASF_LOGGER
from asf_search.CMR import get_additional_fields
from asf_search.export.metalink import MetalinkStreamArray
import xml.etree.ElementTree as ETree

extra_kml_fields = [
    ('configurationName', ['AdditionalAttributes', ('Name', 'BEAM_MODE_DESC'), 'Values', 0]),
    ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
    ('processingTypeDisplay', ['AdditionalAttributes', ('Name', 'PROCESSING_TYPE_DISPLAY'), 'Values', 0]),
    ('sceneDate', ['AdditionalAttributes', ('Name', 'ACQUISITION_DATE'), 'Values', 0]),
    ('shape', ['SpatialExtent', 'HorizontalSpatialDomain', 'Geometry', 'GPolygons', 0, 'Boundary', 'Points']),
    ('thumbnailUrl', ['AdditionalAttributes', ('Name', 'THUMBNAIL_URL'), 'Values', 0]),
    ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
]

def results_to_kml(results):
    ASF_LOGGER.info('Started translating results to kml format')
    
    if inspect.isgeneratorfunction(results) or isinstance(results, GeneratorType):
        return KMLStreamArray(results)
    
    return KMLStreamArray([results])

class KMLStreamArray(MetalinkStreamArray):
    def __init__(self, results):
        MetalinkStreamArray.__init__(self, results)
        self.header = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
 <kml xmlns="http://www.opengis.net/kml/2.2">
   <Document>
     <name>ASF Datapool Search Results</name>
     <description>Search Performed:</description>
     <Style id="yellowLineGreenPoly">
         <LineStyle>
         <color>30ff8800</color>
         <width>4</width>
         </LineStyle>
         <PolyStyle>
         <color>7f00ff00</color>
         </PolyStyle>
     </Style>\n     """
        self.footer = """</Document>\n</kml>"""
        
    def get_additional_fields(self, product):
        umm = product.umm
        additional_fields = {}
        for key, path in extra_kml_fields:
            additional_fields[key] = get_additional_fields(umm, *path)
        return additional_fields

    def getOutputType(self) -> str:
        return 'kml'
    
    def getItem(self, p):
        placemark = ETree.Element("Placemark")
        name = ETree.Element('name')
        name.text = p['sceneName']
        placemark.append(name)
        
        description = ETree.Element('description')
        description.text = """&lt;![CDATA["""
        placemark.append(description)
        
        h1 = ETree.Element('h1')
        h1.text = f"{p['platform']} ({p['configurationName']}), acquired {p['sceneDate']}"
        h2 = ETree.Element('h2')
        h2.text = p.get('url', '')
        description.append(h1)
        description.append(h2)
        
        div = ETree.Element('div', attrib={'style': 'position:absolute;left:20px;top:200px'})
        description.append(div)

        h3 = ETree.Element('h3')
        h3.text = 'Metadata'
        div.append(h3)
        
        ul = ETree.Element('ul')
        div.append(ul)
        
        for text, value in self.metadata_fields(p).items():
            li = ETree.Element('li')
            li.text = text + str(value)
            ul.append(li)
        
        d = ETree.Element('div', attrib={'style': "position:absolute;left:300px;top:250px"})
        description.append(d)
        
        a = ETree.Element('a')
        if p.get('browse') is not None:
            a.set('href', p.get('browse')[0])
        else:
            a.set('href', "")
        
        d.append(a)
        
        img = ETree.Element('img')
        if p.get('thumbnailUrl') is not None:
            img.set('src', p.get('thumbnailUrl'))
        else:
            img.set('src', "None")
        a.append(img)
        
        styleUrl = ETree.Element('styleUrl')
        styleUrl.text = '#yellowLineGreenPoly'
        placemark.append(styleUrl)
        
        polygon = ETree.Element('Polygon')
        placemark.append(polygon)

        extrude = ETree.Element('extrude')
        extrude.text = '1'
        polygon.append(extrude)
        
        altitudeMode = ETree.Element('altitudeMode')
        altitudeMode.text = 'relativeToGround'
        polygon.append(altitudeMode)
        
        outerBondaryIs = ETree.Element('outerBoundaryIs')
        polygon.append(outerBondaryIs)
        
        linearRing = ETree.Element("LinearRing")
        outerBondaryIs.append(linearRing)
        
        coordinates = ETree.Element('coordinates')
        coordinates.text = '\n' + (14 * ' ') + ('\n' + (14 * ' ')).join([f"{c['Longitude']},{c['Latitude']},2000" for c in p['shape']]) + '\n' + (14 * ' ')
        linearRing.append(coordinates)

        self.indent(placemark, 3)
        
        # for CDATA section, manually replace &amp; escape character with &
        return ETree.tostring(placemark, encoding='unicode').replace('&amp;', '&')
    
    # Helper method for getting additional fields in <ul> tag
    def metadata_fields(self, item: dict):
        required = {
            'Processing type: ': item['processingTypeDisplay'],
            'Frame: ': item['frameNumber'],
            'Path: ': item['pathNumber'],
            'Orbit: ': item['orbit'],
            'Start time: ': item['startTime'],
            'End time: ': item['stopTime'],
        }
        
        optional = {}
        for text, key in [('Faraday Rotation: ', 'faradayRotation'), ('Ascending/Descending: ', 'flightDirection'), ('Off Nadir Angle: ', 'offNadirAngle'), ('Pointing Angle: ', 'pointingAngle'), ('Temporal Baseline: ', 'temporalBaseline'), ('Perpendicular Baseline: ', 'perpendicularBaseline')]:
            if item.get(key) is not None:
                if type(item[key]) == float and key == 'offNadirAngle':
                    optional[text] = f'{item[key]:g}' #trim trailing zeros    
                else:
                    optional[text] = item[key]
            elif key not in ['temporalBaseline', 'perpendicularBaseline']:
                optional[text] = 'None'
        
        output = { **required, **optional }
        if item['processingLevel'] == 'BURST':
            burst = {
                'Absolute Burst ID: ' :  item['burst']['absoluteBurstID'],
                'Relative Burst ID: ' :  item['burst']['relativeBurstID'],
                'Full Burst ID: ':  item['burst']['fullBurstID'],
                'Burst Index: ': item['burst']['burstIndex'],
                'Azimuth Time: ': item['burst']['azimuthTime'],
                'Azimuth Anx Time: ': item['burst']['azimuthAnxTime'],
                'Samples per Burst: ': item['burst']['samplesPerBurst'],
                'Subswath: ': item['burst']['subswath']
            }
            
            output = { **output, **burst}
        
        return output