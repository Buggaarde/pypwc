from abc import ABCMeta, abstractmethod
from copy import deepcopy
from datetime import datetime
import os
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom


class Component(object):
    '''Anything that resides in a canvas should be a component
    and any combination of components should themselves be components.
    
    Implements the composite design pattern.'''
    _names = []
    _allowed_component_types = ['SOURCE', 'TARGET', 'EXPRMACRO',
                        'TRANSFORMATION', 'MAPPLET', 'MAPPING',
                        'FOLDER', 'REPOSITORY', 'POWERMART',
                        'COMPOSITE']
    _counter = 0
    def __init__(self, name, component_type):
        self._attributes = {}
        self._fields = []
        self._is_composite = False
        self.is_reusable = 'NO'

        self.parents = []
        self.children = []
        self.connections = []
        self.table_attributes = {}


        assert isinstance(name, str)
        if name in Component._names:
            raise ValueError('name: {} is already in use. Please choose another name.'.format(name))
        else:
            self.name = name
            Component._names.append(name)

        assert isinstance(component_type, str)
        if component_type.upper() not in Component._allowed_component_types:
            raise ValueError('component_type: {0} not an allowed type. Allowed types are\n{1}'.format(component_type, Component._allowed_component_types))
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
        self._attributes = value

    @property
    def table_attribute_fields(self):
        return [('TABLEATTRIBUTE',
                {'NAME': name, 'VALUE': value})
                for name, value in self.table_attributes.items()]

    @property
    def fields(self):
        return self._fields

    @fields.setter
    def fields(self, value):
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
            CompositeComponent.connection_list += [connection]

        return CompositeComponent

    def as_instance(self):
        att = self.attributes
        attribute_dict = {
            'DESCRIPTION': '' if not att['DESCRIPTION'] else att['DESCRIPTION'],
            'NAME': '' if not att['NAME'] else att['NAME'],
            'REUSABLE': '' if not att['REUSABLE'] else att['REUSABLE'],
            'TRANSFORMATION_NAME': '' if not att['NAME'] else att['NAME'],
            'TRANSFORMATION_TYPE': '' if not att['TYPE'] else att['TYPE'],
            'TYPE': '' if not self.component_type else self.component_type
        }
        root = ET.Element('INSTANCE', attrib=attribute_dict)
        return ET.ElementTree(root)

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
            self._add_subelements_to_root(root,
                                 self.fields+self.table_attribute_fields)
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
    def __init__(self, name='Composite', component_type='COMPOSITE',
                 component_list=None, connection_list=None):

        super().__init__(name, component_type)
        
        if component_list is None:
            self._component_list = []
        else:
            assert isinstance(component_list, list), 'Expected a list; was {}'.format(type(component_list))
            self._component_list = component_list


        if self.component_type == 'MAPPLET':
            for component in self.component_list:
                if component.component_type == 'MAPPLET':
                    raise ValueError('Mapplets cannot be nested. Found Mapplet in component_list.')

        if connection_list is None:
            self.connection_list = []
        else:
            assert isinstance(connection_list, list), 'Expected a list; was {}'.format(type(connection_list))
            self.connection_list = connection_list        
       
        for connection in self.connection_list:
            from_component_name = connection['FROMINSTANCE']
            from_component_field = connection['FROMFIELD']
            from_component_type = connection['FROMINSTANCETYPE']            
            to_component_name = connection['TOINSTANCE']
            to_component_field = connection['TOFIELD']
            to_component_type = connection['TOINSTANCETYPE']       

            assert from_component_name in self.component_list_names, \
                    '{} not in component names {}'.format(from_component_name, self.component_list_names)
            assert to_component_name in self.component_list_names, \
                    '{} not in component names'.format(to_component_name)
            FromComponent = [comp for comp in self.component_list
                             if comp.name == from_component_name][0]
            ToComponent = [comp for comp in self.component_list
                             if comp.name == to_component_name][0]

            assert (from_component_field 
                    in FromComponent.get_all_transformfield_names())
            assert (to_component_field 
                    in ToComponent.get_all_transformfield_names())

            if ToComponent not in FromComponent.children:
                FromComponent.children.append(ToComponent)
            if FromComponent not in ToComponent.parents:
                ToComponent.parents.append(FromComponent)
        


        self.sources = []
        self.targets = []
        self.input = []
        self.output = []
        
        self._now = datetime.now()
        year, month, day = self._now.year, self._now.month, self._now.day
        hour, minute, second = self._now.hour, self._now.minute, self._now.second
        self._timestamp = '{:02d}/{:02d}/{} {:02d}:{:02d}:{:02d}'.format(
            month, day, year,
            hour, minute, second
        )
        self.powermart_attributes = {
            'CREATION_DATE': self._timestamp,
            'REPOSITORY_VERSION': '182.91'
            }
        self.repository_attibutes = {
            'NAME': 'Dev_Repository',
            'VERSION': '182',
            'CODEPAGE': 'MS1252',
            'DATABASETYPE': 'Microsoft SQL Server'
        }
        self.folder_attributes = {
            'NAME': 'MDW_KRE',
            'GROUP': '',
            'OWNER': 'BIX_PWC_DEV',
            'SHARED': 'NOTSHARED',
            'DESCRIPTION': '',
            'PERMISSIONS': 'rwx---r--',
            'UUID': 'ba3a066c-b172-4542-82f0-337e40e92b32'
        }

        self.instance_transformations = []

    @property
    def component_list(self):
        pass
    
    @component_list.getter
    def component_list(self):
        return self._component_list

    @component_list.setter
    def component_list(self, new_list):
        s = 'You cannot directly assign values to component_list. Use the add_component().method instead.'
        raise ValueError(s)
    
    def add_component(self, new_component):
        self._component_list.append(new_component)

    def add_components(self, new_components):
        for comp in new_components:
            self._component_list.append(comp)

    @property
    def component_list_names(self):
        return [comp.name for comp in self.component_list]

    def connect(self, FromComponent, ToComponent, connect_dict):
        # Make sure that the two components in fact contain the fields from the dict
        from_fields = FromComponent.get_all_transformfield_names()
        if not set(connect_dict.keys()) <= set(from_fields):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS of FromComponent')
        to_fields = ToComponent.get_all_transformfield_names()
        if not set(connect_dict.values()) <= set(to_fields):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS of ToComponent')

        # Declare children and parents
        if ToComponent not in FromComponent.children:
            FromComponent.children.append(ToComponent)
        if FromComponent not in ToComponent.parents:
            ToComponent.parents.append(FromComponent)

        # Append connection to connection_list
        for key, val in connect_dict.items():
            connection = {
                'FROMFIELD': key,
                'TOFIELD': val,
                'FROMINSTANCE': FromComponent.attributes['NAME'],
                'TOINSTANCE': ToComponent.attributes['NAME'],
                'FROMINSTANCETYPE': FromComponent.attributes['TYPE'],
                'TOINSTANCETYPE': ToComponent.attributes['TYPE']
            }
            self.connection_list.append(connection)

    def get_all_mapplets(self):
        return [comp for comp in self.component_list if isinstance(comp, Mapplet)]

    def get_all_exprmacros(self):
        return [comp for comp in self.component_list
                if comp.component_type == 'EXPRMACRO']

    def get_all_reusable_transformations(self):
        return [comp for comp in self.component_list 
                if (comp.component_type == 'TRANSFORMATION'
                    and self.is_reusable == 'YES')]

    def get_all_connections(self):
        return []

    @property
    def all_non_global_components(self):
        return [comp for comp in self.component_list
                if (
                    comp not in self.get_all_mapplets()
                    and comp not in self.get_all_exprmacros()
                    and comp not in self.get_all_reusable_transformations()
                )]

    def as_xml(self):
        powermart = ET.Element('POWERMART', attrib=self.powermart_attributes)
        repository = ET.Element('REPOSITORY', attrib=self.repository_attibutes)
        folder = ET.Element('FOLDER', attrib=self.folder_attributes)

        powermart.append(repository)
        repository.append(folder)
        root = folder

        for source in self.sources:
            root.append(source.as_xml().getroot())
        for target in self.targets:
            root.append(target.as_xml().getroot())
        for exprmacro in self.get_all_exprmacros():
            root.append(exprmacro.as_xml().getroot())
        for reusable in self.get_all_reusable_transformations():
            root.append(reusable.as_xml().getroot())
        for mapplet in self.get_all_mapplets():
            mapplet_folder = mapplet.as_xml().findall('./REPOSITORY/FOLDER/*')
            for element in mapplet_folder:
                root.append(element)

        instance = ET.Element(self.component_type.upper(), attrib={
            'DESCRIPTION': '{} made with pypwc (contact SBS for more information)'.format(self.component_type.title()),
            'ISVALID': 'YES',
            'NAME': self.name,
            'OBJECTVERSION': '1',
            'VERSIONNUMBER': '1'
        })
        root.append(instance)
        root = instance
    
        for component in self.all_non_global_components:
            root.append(component.as_xml().getroot())
        for component in self.instance_transformations:
            root.append(component.as_xml().getroot())
        for component in self.component_list:
            root.append(component.as_instance().getroot())
        for connection in self.connection_list:
            ET.SubElement(root, 'CONNECTOR', attrib=connection)
        ET.SubElement(root, 'ERPINFO')
        
        return ET.ElementTree(powermart)

    def write(self, path, encoding='utf-8'):
        '''
        Write the result of the as_xml()-method to file, and prepends
        xml version and doctype.

        By default, as_xml() writes a one-lined version of the xml document, 
        so care is taken to prettify the output before writing.
        '''
        
        # Write the one-lined output to a temporary file so as to be able
        # to parse the xml separately later.
        ugly_output = self.as_xml().write('./ugly_tmp.xml', encoding=encoding,
                                            xml_declaration=False)

        # Using the toprettyxml() method doesn't allow for us to specify 
        # neither version, encoding nor doctype. These have to be manually
        # prepended,
        version_and_encoding = '<?xml version="1.0" encoding="Windows-1252"?>\n'
        doctype = '<!DOCTYPE POWERMART SYSTEM "powrmart.dtd">\n'       
        with open('./ugly_tmp.xml', mode='r') as ugly:
            ugly_string = ugly.read()
            reparsed = minidom.parseString(ugly_string)
            with open(path, mode='w', encoding=encoding) as file:
                file.write(version_and_encoding)
                file.write(doctype)

                # toprettyxml() also have the downside of automatically adding
                # a version tag, without the option to disable it. We also have
                # to remove this before writing to file.  
                pretty = reparsed.toprettyxml(indent='    ')
                first_line_in_pretty = pretty.split('\n')[0] + '\n'
                pretty_without_header = pretty.split(first_line_in_pretty)[-1]
                file.write(pretty_without_header)
        os.remove('./ugly_tmp.xml')
        print('Wrote to ' + path)


class Mapping(Composite):
    '''Represents a PowerCenter Mapping transformation'''
    def __init__(self, name, component_list=None, connection_list=None):
        super().__init__(name, component_type='Mapping',
                         component_list=component_list,
                         connection_list=connection_list)
        

class MappletIO(Component):
    '''
    Represents the IO Transformations that Mapplets can contain
    '''
    def __init__(self, name, io_type):
        assert isinstance(io_type, str), 'Expected type str, was {}'.format(type(io_type))
        assert io_type.lower() in ['input', 'output'], 'io_type must be either \'input\' or \'output\''
        if io_type.lower() == 'input':
            super().__init__(name='{}Input'.format(name),
                                component_type='TRANSFORMATION')
            self.attributes = {
                'DESCRIPTION': '',
                'NAME': 'INPUT',
                'OBJECTVERSION': '1',
                'REUSABLE': 'NO',
                'TYPE': 'Input Transformation',
                'VERSIONNUMBER': '1'
            }
        if io_type.lower() == 'output':
            super().__init__(name='{}Output'.format(name),
                                component_type='TRANSFORMATION')
            self.attributes = {
                'DESCRIPTION': '',
                'NAME': 'OUTPUT',
                'OBJECTVERSION': '1',
                'REUSABLE': 'NO',
                'TYPE': 'Output Transformation',
                'VERSIONNUMBER': '1'
            }

class Mapplet(Composite):
    '''Represents a PowerCenter Mapplet transformation'''
    def __init__(self, name, component_list=None, connection_list=None):

        # Input and Output is defined before super().__init__() is called
        # because the components are called in the initaliser.
        self.Input = MappletIO(name=name, io_type='input')

        self.Output = MappletIO(name=name, io_type='output')

        super().__init__(name, component_type='Mapplet',
                         component_list=component_list,
                         connection_list=connection_list)

        self.attributes = {
            'DESCRIPTION': '',  
            'NAME': self.name,
            'OBJECTVERSION': '1',
            'REUSABLE': 'YES',
            'TYPE': 'Mapplet',
            'VERSIONNUMBER': '1'
        }



    @Composite.component_list.getter
    def component_list(self):
        if not self.Input.fields and not self.Output.fields:
            return self._component_list
        elif self.Input.fields and not self.Output.fields:
            return self._component_list + [self.Input]
        elif not self.Input.fields and self.Output.fields:
            return self._component_list + [self.Input]
        else:
            return self._component_list + [self.Input, self.Output]

    @property
    def _input_transformations(self):
        input_fields = []
        for input_field in self.Input.fields:
            input_field = deepcopy(input_field)
            i_f = input_field[1]
            i_f.update({
                'MAPPLETGROUP': 'INPUT',
                'PORTTYPE': 'INPUT',
                'REF_FIELD': i_f['NAME'],
                'REF_INSTANCETYPE': 'Input Transformation'
            })

            input_fields.append(input_field)
        return input_fields

    @property
    def _output_transformations(self):
        output_fields = []
        for output_field in self.Output.fields:
            output_field = deepcopy(output_field)
            o_f = output_field[1]
            o_f.update({
                'MAPPLETGROUP': 'OUTPUT',
                'PORTTYPE': 'OUTPUT',
                'REF_FIELD': o_f['NAME'],
                'REF_INSTANCETYPE': 'Output Transformation'
            })

            output_fields.append(output_field)
        return output_fields

    @property
    def instance_transformations(self):
        pass

    @instance_transformations.getter
    def instance_transformations(self):
        '''
        Mapplets contain a transformation containing information
        about the mapplet itself. This method returns the required
        information about these transformations.
        '''
        InstanceTransformation = Component('Mapplet Transformation{}'.format(Component._counter), 
                                            component_type='TRANSFORMATION')
        Component._counter += 1
        InstanceTransformation.fields = self._input_transformations + self._output_transformations

        InstanceTransformation.attributes = self.attributes
        InstanceTransformation.table_attributes = {
            'Is Active': 'NO',
            'Is Partitionable': 'NO',
            'Form Name': ''}
        return [InstanceTransformation]  

    @instance_transformations.setter
    def instance_transformations(self, value):
        pass  

    def as_instance(self):
        att = self.attributes
        attribute_dict = {
            'DESCRIPTION': '' if not att['DESCRIPTION'] else att['DESCRIPTION'],
            'NAME': '' if not att['NAME'] else att['NAME'],
            'REUSABLE': '' if not att['REUSABLE'] else att['REUSABLE'],
            'TRANSFORMATION_NAME': '' if not att['NAME'] else att['NAME'],
            'TRANSFORMATION_TYPE': '' if not att['TYPE'] else att['TYPE'],
            'TYPE': '' if not self.component_type else self.component_type
        }
        root = ET.Element('INSTANCE', attrib=attribute_dict)
        return ET.ElementTree(root)

    
    

