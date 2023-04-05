import csv
from types import GeneratorType
from asf_search import ASF_LOGGER
from asf_search.CMR.translate import get_additional_fields

from asf_search.export.export_translators import ASFSearchResults_to_properties_list
import inspect

extra_csv_fields = [
    ('sceneDate', ['AdditionalAttributes', ('Name', 'ACQUISITION_DATE'), 'Values', 0]),
    ('nearStartLat', ['AdditionalAttributes', ('Name', 'NEAR_START_LAT'), 'Values', 0]),
    ('nearStartLon', ['AdditionalAttributes', ('Name', 'NEAR_START_LON'), 'Values', 0]),
    ('farStartLat', ['AdditionalAttributes', ('Name', 'FAR_START_LAT'), 'Values', 0]),
    ('farStartLon', ['AdditionalAttributes', ('Name', 'FAR_START_LON'), 'Values', 0]),
    ('nearEndLat', ['AdditionalAttributes', ('Name', 'NEAR_END_LAT'), 'Values', 0]),
    ('nearEndLon', ['AdditionalAttributes', ('Name', 'NEAR_END_LON'), 'Values', 0]),
    ('farEndLat', ['AdditionalAttributes', ('Name', 'FAR_END_LAT'), 'Values', 0]),
    ('farEndLon', ['AdditionalAttributes', ('Name', 'FAR_END_LON'), 'Values', 0]),
    ('faradayRotation', ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0]),
    ('configurationName', ['AdditionalAttributes', ('Name', 'BEAM_MODE_DESC'), 'Values', 0]),
    ('doppler', ['AdditionalAttributes', ('Name', 'DOPPLER'), 'Values', 0]),
    ('sizeMB', ['DataGranule', 'ArchiveAndDistributionInformation', 0, 'Size']),
    ('insarStackSize', ['AdditionalAttributes', ('Name', 'INSAR_STACK_SIZE'), 'Values', 0]),
]

fieldnames = (
    "Granule Name",
    "Platform",
    "Sensor",
    "Beam Mode",
    "Beam Mode Description",
    "Orbit",
    "Path Number",
    "Frame Number",
    "Acquisition Date",
    "Processing Date",
    "Processing Level",
    "Start Time",
    "End Time",
    "Center Lat",
    "Center Lon",
    "Near Start Lat",
    "Near Start Lon",
    "Far Start Lat",
    "Far Start Lon",
    "Near End Lat",
    "Near End Lon",
    "Far End Lat",
    "Far End Lon",
    "Faraday Rotation",
    "Ascending or Descending?",
    "URL",
    "Size (MB)",
    "Off Nadir Angle",
    "Stack Size",
    "Doppler",
    "GroupID",
    "Pointing Angle",
    "TemporalBaseline",
    "PerpendicularBaseline",
    "relativeBurstID",
    "absoluteBurstID",
    "fullBurstID",
    "burstIndex",
    "azimuthTime",
    "azimuthAnxTime",
    "samplesPerBurst",
    "subswath"
)

def results_to_csv(results):
    ASF_LOGGER.info("started translating results to csv format")
    
    if inspect.isgeneratorfunction(results) or isinstance(results, GeneratorType):
        return CSVStreamArray(results)
    
    return CSVStreamArray([results])

class CSVStreamArray(list):
    def __init__(self, results):
        self.pages = results
        self.len = 1

    def __iter__(self):
        return self.streamRows()

    def __len__(self):
        return self.len

    def get_additional_output_fields(self, product):
        umm = product.umm

        additional_fields = {}
        for key, path in extra_csv_fields:
            additional_fields[key] = get_additional_fields(umm, *path)

        return additional_fields

    def streamRows(self):

        f = CSVBuffer()
        writer = csv.DictWriter(f, quoting=csv.QUOTE_ALL, fieldnames=fieldnames)     
        yield writer.writeheader()
        
        completed = False
        for page_idx, page in enumerate(self.pages):
            ASF_LOGGER.info(f"Streaming {len(page)} products from page {page_idx}")
            completed = page.searchComplete
            
            properties_list = ASFSearchResults_to_properties_list(page, self.get_additional_output_fields)
            yield from [writer.writerow(self.getItem(p)) for p in properties_list]

        if not completed:
            ASF_LOGGER.warn('Failed to download all results from CMR')
        
        ASF_LOGGER.info('Finished streaming csv results')
            
    def getItem(self, p):
        return {
            "Granule Name":p['sceneName'],
            "Platform":p['platform'],
            "Sensor":p['sensor'],
            "Beam Mode":p['beamModeType'],
            "Beam Mode Description":p['configurationName'],
            "Orbit":p['orbit'],
            "Path Number":p['pathNumber'],
            "Frame Number":p['frameNumber'],
            "Acquisition Date":p['sceneDate'],
            "Processing Date":p['processingDate'],
            "Processing Level":p['processingLevel'],
            "Start Time":p['startTime'],
            "End Time":p['stopTime'],
            "Center Lat":p['centerLat'],
            "Center Lon":p['centerLon'],
            "Near Start Lat":p['nearStartLat'],
            "Near Start Lon":p['nearStartLon'],
            "Far Start Lat":p['farStartLat'],
            "Far Start Lon":p['farStartLon'],
            "Near End Lat":p['nearEndLat'],
            "Near End Lon":p['nearEndLon'],
            "Far End Lat":p['farEndLat'],
            "Far End Lon":p['farEndLon'],
            "Faraday Rotation":p['faradayRotation'],
            "Ascending or Descending?":p['flightDirection'],
            "URL":p['url'],
            "Size (MB)":p['sizeMB'],
            "Off Nadir Angle":p['offNadirAngle'],
            "Stack Size":p['insarStackSize'],
            "Doppler":p['doppler'],
            "GroupID":p['groupID'],
            "Pointing Angle":p['pointingAngle'],
            "TemporalBaseline":p.get('teporalBaseline'),
            "PerpendicularBaseline":p.get('pependicularBaseline'),
            "relativeBurstID":  p['burst']['relativeBurstID'] if p['processingLevel'] == 'BURST' else None,
            "absoluteBurstID":  p['burst']['absoluteBurstID'] if p['processingLevel'] == 'BURST' else None,
            "fullBurstID":  p['burst']['fullBurstID'] if p['processingLevel'] == 'BURST' else None,
            "burstIndex":   p['burst']['burstIndex'] if p['processingLevel'] == 'BURST' else None,
            "azimuthTime": p['burst']['azimuthTime'] if p['processingLevel'] == 'BURST' else None,
            "azimuthAnxTime": p['burst']['azimuthAnxTime'] if p['processingLevel'] == 'BURST' else None,
            "samplesPerBurst":  p['burst']['samplesPerBurst'] if p['processingLevel'] == 'BURST' else None,
            "subswath": p['burst']['subswath'] if p['processingLevel'] == 'BURST' else None
        }

class CSVBuffer:
# https://docs.djangoproject.com/en/3.2/howto/outputting-csv/#streaming-large-csv-files
# A dummy CSV buffer to be used by the csv.writer class, returns the 
# formatted csv row "written" to it when writer.writerow/writeheader is called
    
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value
