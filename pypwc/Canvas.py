from abc import ABCMeta, abstractmethod
import os
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom

class Component(object):
    '''Anything that resides in a canvas should be a component
    and any combination of components should themselves be components.
    
    Implements the composite design pattern.'''
    _names = []
    _allowed_types = ['SOURCE', 'TARGET', 'EXPRMACRO',
                        'TRANSFORMATION', 'MAPPLET', 'MAPPING',
                        'FOLDER', 'REPOSITORY', 'POWERMART',
                        'COMPOSITE']
    def __init__(self,*, name, component_type):
        self._attributes = {}
        self._fields = []
        self._is_composite = False

        self.parents = []
        self.children = []
        self.connections = []

        assert isinstance(name, str)
        if name in Component._names:
            raise ValueError('name: {} is already in use. Please choose another name.'.format(name))
        else:
            self.name = name
            Component._names.append(name)

        assert isinstance(component_type, str)
        if component_type.upper() not in Component._allowed_types:
            raise ValueError('component_type: {0} not an allowed type. Allowed types are\n{1}'.format(component_type, Component._allowed_types))
        else:
            self.component_type = component_type.upper()

    @property
    def is_composite(self):
        return self._is_composite

    @is_composite.setter
    def is_composite(self, value):
        assert isinstance(value, bool)
        if value == True:
            if self.fields:
                raise ValueError('It makes no sense for composite components to have fields. Found the following fields:\n{}'.format(self.fields))
            elif self.attributes:
                raise ValueError('It makes no sense for composite components to have attributes. Found the following attributes:\n{}'.format(self.attributes))
            else: # value = true
                self._is_composite = value
        else: # value = false
            self._is_composite = value

    @property
    def attributes(self):
        return self._attributes

    @attributes.setter
    def attributes(self, value):
        if self.is_composite:
            raise ValueError('The Component is composite. Composite components should have no attributes.')
        else:
            self._attributes = value

    @property
    def fields(self):
        return self._fields

    @fields.setter
    def fields(self, value):
        if self.is_composite:
            raise ValueError('The Component is composite. Composite Components should have no fields.')
        else:
            self._fields = value


    def _field_format_is_valid(self, field):
        '''field must be of the form
        (NAME, attrib_dict[, [nested_fields]])
        '''
        if not isinstance(field, tuple):
            msg = 'field is not a tuple'
            return (False, msg)
        if not (len(field) == 2 or len(field) == 3):
            msg = 'The length of the tuple must be 2 or 3'
            return (False, msg)
        if len(field) == 2:
            if not isinstance(field[0], str):
                msg = 'Index 0 of field must be a string'
                return (False, msg)
            if not isinstance(field[1], dict):
                msg = 'Index 1 of field must be a dictionary'                
                return (False, msg)
        elif len(field) == 3:
            if not isinstance(field[0], str):
                msg = 'Index 0 of field must be a string'                
                return (False, msg)
            if not isinstance(field[1], dict):
                msg = 'Index 1 of field must be a dictionary'                                
                return (False, msg)
            if not isinstance(field[2], list):
                msg = 'Index 2 of field must be a list'                                
                return (False, msg)
            else:
                nested_fields = field[2]
                for nested_field in nested_fields:
                    nested_is_valid, nested_msg = self._field_format_is_valid(nested_field)
                    if not nested_is_valid:
                        msg = 'Nested in {0}: {1}'.format(field, nested_msg)
                        return (False, nested_msg)
        msg = 'The format is valid'
        return (True, msg)

    def add_field(self, field):
        is_valid, msg = self._field_format_is_valid(field)
        if not is_valid:
            raise TypeError('Field format is incorrect with the following error message:\n{}'.format(msg))
        else:
            self.fields.append(field)

    def add_fields(self, fields):
        if not hasattr(fields, '__iter__'):
            raise TypeError('add_fields must be provided an iterable')
        else:
            for field in fields:
                self.add_field(field)

    def get_all_fields_of_type(self, fieldtype):
        return [f for f in self.fields if f[0] == fieldtype]     

    def get_all_transformfields(self):
        return self.get_all_fields_of_type('TRANSFORMFIELD')

    def get_all_transformfield_names(self):
        return [tff[1]['NAME'] for tff in self.get_all_transformfields()]

    def connect_to(self, OtherComponent, connect_dict):
        '''
        OtherComponent becomes the child of the calling Component
        '''
        # Make sure that the two components in fact contain the fields from the dict
        self_fields = self.get_all_transformfield_names()
        if not set(connect_dict.keys()) <= set(self_fields):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS')
        other_fields = OtherComponent.get_all_transformfield_names()
        if not set(connect_dict.values()) <= set(other_fields):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS')

        # Declare children and parents
        self.children.append(OtherComponent)
        OtherComponent.parents.append(self)

        # Construct a new Component with the composite data, and return
        CompositeComponent = Composite(component_list=[self, OtherComponent])
        CompositeComponent.is_composite = True
        for key, val in connect_dict.items():
            connection = {
                'FROMFIELD': key,
                'TOFIELD': val,
                'FROMINSTANCE': self.attributes['NAME'],
                'TOINSTANCE': OtherComponent.attributes['NAME'],
                'FROMINSTANCETYPE': self.attributes['TYPE'],
                'TOINSTANCETYPE': OtherComponent.attributes['TYPE']
            }
            CompositeComponent.connection_list.append(connection)

        return CompositeComponent



    def _add_subelements_to_root(self, root, fields):
        for f in fields:
            assert isinstance(f, tuple), 'f is type {}'.format(type(f))
            assert (len(f) == 2 or len(f) == 3), 'Length of fields-tuple is {}\n{}'.format(len(f), f)
            if len(f) == 2: # No nested fields
                fieldtype, attrib_dict = f
                ET.SubElement(root, fieldtype, attrib=attrib_dict)
            elif len(f) == 3: # Yes nested fields
                fieldtype, attrib_dict, nested_fields = f
                local_root = ET.Element(fieldtype, attrib=attrib_dict)
                self._add_subelements_to_root(local_root, nested_fields)
                root.append(local_root)


    def as_xml(self):
        '''Returns an ElementTree with the apppropriate children
        and attributes.'''
        if not self.is_composite:
            root = ET.Element(self.component_type, attrib=self.attributes)
            self._add_subelements_to_root(root, self.fields)
            TREE = ET.ElementTree(root)
            return TREE
        else:   # In the Component base class, the returned XML of composite
                # Components is wrapped in a <COMPOSITE /> tag. This behaviour
                # is assumed to be overwritten in components of type MAPPING
                # and MAPPLET.
            raise NotImplementedError('Not currently prioritized. As it stands right now, there is no real reason to handle the xml structure of composite Components.')

    def write(self, path, encoding='utf-8'):
        '''
        Reparse the one-lined default xml and write the prettified version to path.
        '''
        
        ugly_output = self.as_xml().write('./ugly_tmp.xml', encoding=encoding,
                                            xml_declaration=False)

        # Using the toprettyxml() method doesn't allow for us to specify 
        # neither version/encoding nor doctype. These have to be manually added
        # before the fact.
        version_and_encoding = '<?xml version="1.0" encoding="Windows-1252"?>\n'
        doctype = '<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n'       
        with open('./ugly_tmp.xml', mode='r') as ugly:
            ugly_string = ugly.read()
            reparsed = minidom.parseString(ugly_string)
            with open(path, mode='w', encoding=encoding) as file:
                file.write(version_and_encoding)
                file.write(doctype)

                # toprettyxml() also have the downside of automatically a version tag,
                # without the option to disable it. We also have to remove this before
                # writing to file.  
                pretty = reparsed.toprettyxml(indent='    ')
                first_line_in_pretty = pretty.split('\n')[0] + '\n'
                pretty_without_header = pretty.split(first_line_in_pretty)[-1]
                file.write(pretty_without_header)
        os.remove('./ugly_tmp.xml')


class Composite(Component):
    '''pass'''
    def __init__(self, component_list=[], connection_list=[]):
        self.component_list = component_list
        self.connection_list = connection_list
        super().__init__(name='Composite', component_type='COMPOSITE')

    def as_xml(self):
        root = ET.Element('COMPOSITE')
        for component in self.component_list:
            comp_root = component.as_xml().getroot()
            root.append(comp_root)
        for component in self.component_list:
            att = component.attributes
            instance_attributes = {
                'DESCRIPTION': '' if not att['DESCRIPTION'] else att['DESCRIPTION'],
                'NAME': '' if not att['NAME'] else att['NAME'],
                'REUSABLE': '' if not att['REUSABLE'] else att['REUSABLE'],
                'TRANSFORMATION_NAME': '' if not att['NAME'] else att['NAME'],
                'TRANSFORMATION_TYPE': '' if not att['TYPE'] else att['TYPE'],
                'TYPE': '' if not component.component_type else component.component_type 
            }
            ET.SubElement(root, 'INSTANCE', attrib=instance_attributes)
        for connection in self.connection_list:
            ET.SubElement(root, 'CONNECTOR', attrib=connection)
        return ET.ElementTree(root)

    def write(self, path, encoding='utf-8'):
        '''
        Reparse the one-lined default xml and write the prettified version to path.
        '''
        
        ugly_output = self.as_xml().write('./ugly_tmp.xml', encoding=encoding,
                                            xml_declaration=False)

        # Using the toprettyxml() method doesn't allow for us to specify 
        # neither version, encoding nor doctype. These have to be manually added
        # before the fact.
        version_and_encoding = '<?xml version="1.0" encoding="Windows-1252"?>\n'
        doctype = '<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n'       
        with open('./ugly_tmp.xml', mode='r') as ugly:
            ugly_string = ugly.read()
            reparsed = minidom.parseString(ugly_string)
            with open(path, mode='w', encoding=encoding) as file:
                file.write(version_and_encoding)
                file.write(doctype)

                # toprettyxml() also have the downside of automatically a version tag,
                # without the option to disable it. We also have to remove this before
                # writing to file.  
                pretty = reparsed.toprettyxml(indent='    ')
                first_line_in_pretty = pretty.split('\n')[0] + '\n'
                pretty_without_header = pretty.split(first_line_in_pretty)[-1]
                file.write(pretty_without_header)
        os.remove('./ugly_tmp.xml')


class Mapping(Composite):
    '''Docstring'''
    def __init__(self, component_list=[]):
        super().__init__(component_list)
    
    def write(self, path, encoding='utf-8'):
        '''
        Reparse the one-lined default xml and write the prettified version to path.
        '''
        
        ugly_output = self.as_xml().write('./ugly_tmp.xml', encoding=encoding,
                                            xml_declaration=False)

        # Using the toprettyxml() method doesn't allow for us to specify 
        # neither version, encoding nor doctype. These have to be manually added
        # before the fact.
        version_and_encoding = '<?xml version="1.0" encoding="Windows-1252"?>\n'
        doctype = '<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n'       
        with open('./ugly_tmp.xml', mode='r') as ugly:
            ugly_string = ugly.read()
            reparsed = minidom.parseString(ugly_string)
            with open(path, mode='w', encoding=encoding) as file:
                file.write(version_and_encoding)
                file.write(doctype)

                # toprettyxml() also have the downside of automatically a version tag,
                # without the option to disable it. We also have to remove this before
                # writing to file.  
                pretty = reparsed.toprettyxml(indent='    ')
                first_line_in_pretty = pretty.split('\n')[0] + '\n'
                pretty_without_header = pretty.split(first_line_in_pretty)[-1]
                file.write(pretty_without_header)
        os.remove('./ugly_tmp.xml')


    

