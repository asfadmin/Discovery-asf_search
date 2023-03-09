import inspect
from types import GeneratorType
import xml.etree.ElementTree as ETree
from asf_search import ASF_LOGGER
from asf_search.export.export_translators import ASFSearchResults_to_properties_list

def results_to_metalink(results):
    ASF_LOGGER.info('Started translating results to metalink format')
    
    if inspect.isgeneratorfunction(results) or isinstance(results, GeneratorType):
        return MetalinkStreamArray(results)
    
    return MetalinkStreamArray([results])

class MetalinkStreamArray(list):
    def __init__(self, results):
        self.pages = results
        self.len = 1
        self.header = """<?xml version="1.0"?>
<metalink xmlns="http://www.metalinker.org/" version="3.0">
    <publisher><name>Alaska Satellite Facility</name><url>http://www.asf.alaska.edu/</url></publisher>
    <files>"""

        self.footer = """
    </files>\n</metalink>"""

    def get_additional_fields(self, product):
        return {}
    
    def __iter__(self):
        return self.streamPages()

    def __len__(self):
        return self.len

    def streamPages(self):
        yield self.header
        
        completed = False
        for page_idx, page in enumerate(self.pages):
            ASF_LOGGER.info(f"Streaming {len(page)} products from page {page_idx}")
            completed = page.searchComplete
            
            properties_list = ASFSearchResults_to_properties_list(page, self.get_additional_fields)
            yield from [self.getItem(p) for p in properties_list]
        
        if not completed:
            ASF_LOGGER.warn('Failed to download all results from CMR')
        
        yield self.footer
        
        ASF_LOGGER.info(f"Finished streaming {self.getOutputType()} results")
        

    def getOutputType(self) -> str:
        return 'metalink'
    
    def getItem(self, p):
        file = ETree.Element("file", attrib={'name': p['fileName']})
        resources = ETree.Element('resources')

        url = ETree.Element('url', attrib={'type': 'http'})
        url.text = p['url']
        resources.append(url)
        file.append(resources)
        
        if p['md5sum'] and p['md5sum'] != 'NA':
            verification = ETree.Element('verification')
            h = ETree.Element('hash', {'type': 'md5'})
            h.text = p['md5sum']
            verification.append(h)
            file.append(verification)
            
        if p['bytes'] and p['bytes'] != 'NA':
            size = ETree.Element('size')
            size.text = str(p['bytes'])
            file.append(size)
        
        return '\n' + (8*' ') + ETree.tostring(file, encoding='unicode')

    def indent(self, elem, level=0):
        # Only Python 3.9+ has a built-in indent function for element tree.
        # https://stackoverflow.com/a/33956544
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i