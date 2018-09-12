from pypwc.Canvas import Mapping, Mapplet, MappletIO
from pypwc.Transformations import *

import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom

from collections import Counter

def component_from_xml(elementTree, xpath):
    pass

def from_xml(path):
    '''
    Imports xml file into a pypwc datastructure reflecting the
    PowerCenter construction.
    '''
    pwc = ET.parse(path)
    root = pwc.getroot()
    folder_content = root.findall('REPOSITORY/FOLDER/*')
    top_level_folder_content = Counter([child.tag for child in folder_content])

    m_ = component_from_xml(folder_content.findall('./MAPPING'))
    non_mappings = (child.tag for child in folder_content if child.tag != 'MAPPING')
    for component in non_mappings:
        print(component)
        m_.add_component(component_from_xml(component))
    

if __name__ == '__main__':
    path = r'./m_test.xml'
    from_xml(path)