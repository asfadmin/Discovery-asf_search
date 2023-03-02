# import logging
# from typing import Dict, List
import xml.etree.ElementTree as ETree

from asf_search.export.export_translators import ASFSearchResults_to_properties_list


# def ASFSearchResults_to_metalink(products: List[Dict]):
#     logging.debug('translating: metalink')

#     templateEnv = Environment(
#         loader=PackageLoader('asf_search.export', 'templates'),
#         autoescape=True
#     )

#     template = templateEnv.get_template('template.metalink')
#     for line in template.stream(results=products):
#         yield line


class XMLStreamArray(list):
    def __init__(self, results):
        self.pages = results
        self.len = 1
        self.header = """<?xml version="1.0"?><metalink xmlns="http://www.metalinker.org/" version="3.0">
        <publisher><name>Alaska Satellite Facility</name><url>http://www.asf.alaska.edu/</url></publisher>
        <files>"""

        self.footer = "</files>\n</metalink>"

    def get_additional_fields(self, product):
        return {}
    
    def __iter__(self):
        return self.streamPages()

    def __len__(self):
        return self.len

    def streamPages(self):
        # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.iterparse
        yield self.header
        for page in self.pages:
            properties_list = ASFSearchResults_to_properties_list(page, self.get_additional_fields)
            yield [self.getItem(p) for p in properties_list]
        
        yield self.footer

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
        
        ETree.indent(file)
        return '\n' + ETree.tostring(file, encoding='unicode')
    
        # <file name="{{ r['fileName'] }}">
        #     # <resources>
        #     #     <url type="http">{{ r['url'] }}</url>
        #     # </resources>

        #     {% if r['md5sum'] and r['md5sum'] != 'NA' %}
        #         <verification>
        #             <hash type="md5">{{ r['md5sum'] }}</hash>
        #         </verification>
        #     {% endif %}

        #     {% if r['bytes'] and r['bytes'] != 'NA' %}
        #         <size>{{ r['bytes'] }}</size>
        #     {% endif %}
        # </file>
