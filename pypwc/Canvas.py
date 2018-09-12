from abc import ABCMeta, abstractmethod
from copy import deepcopy
from datetime import datetime
import os
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom

__author__ = 'Simon Bugge Siggaard'
__email__ = 'sbs@bec.dk'

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
        self.valid_field_attribute_names = []


        assert isinstance(name, str)
        # if name in Component._names:
        #     raise ValueError('name: {} is already in use. Please choose another name.'.format(name))
        # else:
        #     self.name = name
        #     Component._names.append(name)
        self.name = name
        Component._names.append(name)

        assert isinstance(component_type, str)
        if component_type.upper() not in Component._allowed_component_types:
            raise ValueError('component_type: {0} not an allowed type. Allowed types are\n{1}'.format(component_type, Component._allowed_component_types))
        else:
            self.component_type = component_type.upper()

        # self.input = {'input': self}
        # self.output = {'output': self}

    @property
    def is_composite(self):
        return self._is_composite

    @is_composite.setter
    def is_composite(self, value):
        assert isinstance(value, bool)
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
        pass


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
            # We want to purge incoming fields for attributes that
            # are invalid
            att = field[1]
            new_att = {}
            for valid_attribute in self.valid_field_attribute_names:
                new_att[valid_attribute] = att[valid_attribute]

            if len(field) == 2:
                new_field = (field[0], new_att)
            elif len(field) == 3:
                new_field = (field[0], new_att, field[2])

            self.fields.append(new_field)

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

    def get_all_ifields(self):
        if self.component_type == 'SOURCE':
            return []
        elif self.component_type == 'TARGET':
            return self.get_all_fields_of_type('TARGETFIELD')
        else:
            return [tff for tff in self.get_all_transformfields() if 'INPUT' in tff[1]['PORTTYPE']]

    def get_all_ofields(self):
        if self.component_type == 'SOURCE':
            return self.get_all_fields_of_type('SOURCEFIELD')
        elif self.component_type == 'TARGET':
            return []
        else:
            return [tff for tff in self.get_all_transformfields() if 'OUTPUT' in tff[1]['PORTTYPE']]
        
    def get_all_iofields(self):
        if self.component_type == 'SOURCE':
            return self.get_all_fields_of_type('SOURCEFIELD')
        elif self.component_type == 'TARGET':
            return self.get_all_fields_of_type('TARGETFIELD')
        else:
            return [tff for tff in self.get_all_transformfields() if 'INPUT/OUTPUT' in tff[1]['PORTTYPE']]

    def replace_field(self, old_field, new_field):
        index_of_old = self.fields.index(old_field)
        self.fields[index_of_old] = new_field

    def replace_field_by_name(self, old_name, new_field):
        old_field = [tf for tf in self.get_all_transformfields() if tf[1]['NAME'] == old_name][0]
        self.replace_field(old_field, new_field)


    def remove_field(self, field):
        self.fields.remove(field)
        

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
                pretty = reparsed.toprettyxml(indent='  ')
                first_line_in_pretty = pretty.split('\n')[0] + '\n'
                pretty_without_header = pretty.split(first_line_in_pretty)[-1]
                file.write(pretty_without_header)
        os.remove('./ugly_tmp.xml')


class Composite(Component):
    '''pass'''
    _now = datetime.now()
    year, month, day = _now.year, _now.month, _now.day
    hour, minute, second = _now.hour, _now.minute, _now.second
    _timestamp = '{:02d}/{:02d}/{} {:02d}:{:02d}:{:02d}'.format(
        month, day, year,
        hour, minute, second
    )
    powermart_attributes = {
        'CREATION_DATE': _timestamp,
        'REPOSITORY_VERSION': '182.91'
        }
    repository_attibutes = {
        'NAME': 'Dev_Repository',
        'VERSION': '182',
        'CODEPAGE': 'MS1252',
        'DATABASETYPE': 'Microsoft SQL Server'
    }
    folder_attributes = {
        'NAME': 'MDW_KRE',
        'GROUP': '',
        'OWNER': 'BIX_PWC_DEV',
        'SHARED': 'NOTSHARED',
        'DESCRIPTION': '',
        'PERMISSIONS': 'rwx---r--',
        'UUID': 'ba3a066c-b172-4542-82f0-337e40e92b32'
    }

    def __init__(self, name='Composite', component_type='COMPOSITE',
                 component_list=None, connection_list=None):

        super().__init__(name, component_type)

        self.sources = []
        self.targets = []
        self.mapping_variables = []
        self.composites = []

        self.input = {}
        self.output = {}

        if connection_list is None:
            connection_list = []
        assert isinstance(connection_list, list), 'Expected a list; was {}'.format(type(connection_list))
        self._connection_list = []
        self.add_connections(connection_list)

        if component_list is None:
            component_list = []
        assert isinstance(component_list, list), 'Expected a list; was {}'.format(type(component_list))
        self._component_list = []
        self.add_components(component_list)

        if self.component_type == 'MAPPLET':
            for component in self.component_list:
                if component.component_type == 'MAPPLET':
                    raise ValueError('Mapplets cannot be nested. Found Mapplet in component_list.\n{}'.format(self.component_list))

        

        for connection in self._connection_list:
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
            FromComponent = [comp for comp in self._component_list
                             if comp.name == from_component_name][0]
            ToComponent = [comp for comp in self._component_list
                             if comp.name == to_component_name][0]

            assert (from_component_field
                    in FromComponent.get_all_transformfield_names())
            assert (to_component_field
                    in ToComponent.get_all_transformfield_names())

            if ToComponent not in FromComponent.children:
                FromComponent.children.append(ToComponent)
            if FromComponent not in ToComponent.parents:
                ToComponent.parents.append(FromComponent)

        self.attributes['DESCRIPTION'] = 'Composite made with pypwc (contact SBS for more information)'

        self.instance_transformations = []

        


    @property
    def component_list(self):
        pass

    @component_list.getter
    def component_list(self):
        return self._component_list

    @component_list.setter
    def component_list(self, new_list):
        s = 'You cannot directly assign values to component_list. Use the add_component()-method instead.'
        raise ValueError(s)

    @property
    def connection_list(self):
        pass

    @connection_list.getter
    def connection_list(self):
        return self._connection_list

    @connection_list.setter
    def connection_list(self, new_list):
        s = 'You cannot directly assign values to connection_list. Use the add_connection()-method instead.'
        raise ValueError(s)
        

    def add_component(self, new_component):
        '''
        Add components to component_list. If new_component is Composite, add the components of new_component
        to component_list and add connections of new_component to connection_list. 
        '''
        if new_component.component_type == 'COMPOSITE':
            self.add_components(new_component.component_list)
            self.add_connections(new_component.connection_list)
            self.composites.append(new_component)
        elif new_component.component_type == 'TARGET':
            if new_component not in self._component_list:
                self.targets.append(new_component)
                self._component_list.append(new_component)
        elif new_component.component_type == 'SOURCE':
            if new_component not in self._component_list:
                self.sources.append(new_component)
                self._component_list.append(new_component)
        else:
            if new_component not in self._component_list:
                self._component_list.append(new_component)

    def add_components(self, new_components):
        for comp in new_components:
            self.add_component(comp)

    def add_connection(self, new_connection):
        self._connection_list.append(new_connection)

    def add_connections(self, new_connections):
        for conn in new_connections:
            self.add_connection(conn)

    @property
    def component_list_names(self):
        return [comp.name for comp in self.component_list]

    def connect(self, FromComponent, ToComponent, connect_dict):
        from_field_type = 'SOURCEFIELD' \
                if FromComponent.component_type == 'SOURCE' else 'TRANSFORMFIELD'
        to_field_type = 'TARGETFIELD' \
                if ToComponent.component_type == 'TARGET' else 'TRANSFORMFIELD'

        # Make sure that the two components in fact contain the fields from the dict
        from_fields = FromComponent.get_all_fields_of_type(from_field_type)
        from_names = [ff[1]['NAME'] for ff in from_fields]
        if not set(connect_dict.keys()) <= set(from_names):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS of FromComponent')
        to_fields = ToComponent.get_all_fields_of_type(to_field_type)
        to_names = [tf[1]['NAME'] for tf in to_fields]        
        if not set(connect_dict.values()) <= set(to_names):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS of ToComponent')

        if connect_dict:
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

            # Declare children and parents
            if ToComponent not in FromComponent.children:
                FromComponent.children.append(ToComponent)
            if FromComponent not in ToComponent.parents:
                ToComponent.parents.append(FromComponent)

    def connect_by_name(self, FromComponent, ToComponent):
        from_field_type = 'SOURCEFIELD' \
                if FromComponent.component_type == 'SOURCE' else 'TRANSFORMFIELD'
        to_field_type = 'TARGETFIELD' \
                if ToComponent.component_type == 'TARGET' else 'TRANSFORMFIELD'

        from_field_names = [fc[1]['NAME']
            for fc in FromComponent.get_all_fields_of_type(from_field_type)
            ]
        to_field_names = [fc[1]['NAME']
            for fc in ToComponent.get_all_fields_of_type(to_field_type)
            ]

        common_names = set(from_field_names).intersection(to_field_names)
        connect_dict = dict(zip(common_names, common_names))
        self.connect(FromComponent, ToComponent, connect_dict=connect_dict)

    def connect_by_index(self, FromComponent, ToComponent):
        def _name(field):
            return field[1]['NAME']

        from_field_names = map(_name, FromComponent.get_all_ofields())
        to_field_names = map(_name, ToComponent.get_all_ifields())

        self.connect(FromComponent, ToComponent,
                     connect_dict=dict(zip(from_field_names, to_field_names)))

    def remove_connection(self, output_tuple, input_tuple):
        output_name = output_tuple[0].name
        output_field = output_tuple[1]
        input_name = input_tuple[0].name
        input_field = input_tuple[1]
        def _is_valid_connection(connection):
            if (connection['FROMFIELD'] == output_field
                and connection['TOFIELD'] == input_field
                and connection['FROMINSTANCE'] == output_name
                and connection['TOINSTANCE'] == input_name):
                return True
            else:
                return False

        connection_index = list(map(_is_valid_connection, self.connection_list)).index(True)
        self.connection_list.remove(self.connection_list[connection_index])

    def remove_all_connections_to(self, component, field_name):
        connections = [c for c in self.connection_list
                         if c['TOFIELD'] == field_name and c['TOINSTANCE'] == component.name]
        for c in connections:
            self.connection_list.remove(c)
    
    def remove_all_connections_from(self, component, field_name):
        connections = [c for c in self.connection_list
                         if c['FROMFIELD'] == field_name and c['FROMINSTANCE'] == component.name]
        for c in connections:
            self.connection_list.remove(c)
            
            

        # connection = {
        #             'FROMFIELD': key,
        #             'TOFIELD': val,
        #             'FROMINSTANCE': FromComponent.attributes['NAME'],
        #             'TOINSTANCE': ToComponent.attributes['NAME'],
        #             'FROMINSTANCETYPE': FromComponent.attributes['TYPE'],
        #             'TOINSTANCETYPE': ToComponent.attributes['TYPE']
        #         }

        

    def get_all_mapplets(self):
        return [comp for comp in self.component_list if isinstance(comp, Mapplet)]

    def get_all_exprmacros(self):
        return [comp for comp in self.component_list
                if comp.component_type == 'EXPRMACRO']

    def get_all_reusable_transformations(self):
        return [comp for comp in self.component_list
                if (comp.component_type == 'TRANSFORMATION'
                    and self.is_reusable == 'YES')]

    @property
    def composite_components(self):
        return [comp for comp in self.component_list
                if comp.component_type == 'COMPOSITE']

    def get_all_connections(self):
        return []

    @property
    def all_non_global_components(self):
        return [comp for comp in self.component_list
                if (
                    comp not in self.get_all_mapplets()
                    and comp not in self.targets
                    and comp not in self.sources
                    and comp not in self.get_all_exprmacros()
                    and comp not in self.get_all_reusable_transformations()
                    and comp not in self.composite_components
                )]

    def as_xml(self):
        powermart = ET.Element('POWERMART', attrib=Composite.powermart_attributes)
        repository = ET.Element('REPOSITORY', attrib=Composite.repository_attibutes)
        folder = ET.Element('FOLDER', attrib=Composite.folder_attributes)

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
            'DESCRIPTION': self.attributes['DESCRIPTION'],
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
        for component in self.targets:
            root.append(component.load_order.getroot())
        for variable_field in self.mapping_variables:
            ET.SubElement(root, 'MAPPINGVARIABLE', attrib=variable_field[1])
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
                pretty = reparsed.toprettyxml(indent='  ')
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
        self.attributes['DESCRIPTION'] = 'Mapping made with pypwc (contact SBS for more information)'

    def connect(self, FromComponent, ToComponent, connect_dict):
        from_field_type = 'SOURCEFIELD' \
                if FromComponent.component_type == 'SOURCE' else 'TRANSFORMFIELD'
        to_field_type = 'TARGETFIELD' \
                if ToComponent.component_type == 'TARGET' else 'TRANSFORMFIELD'

        # Make sure that the two components in fact contain the fields from the dict
        from_fields = FromComponent.get_all_fields_of_type(from_field_type)
        from_names = [ff[1]['NAME'] for ff in from_fields]
        if not set(connect_dict.keys()) <= set(from_names):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS of FromComponent')
        to_fields = ToComponent.get_all_fields_of_type(to_field_type)
        to_names = [tf[1]['NAME'] for tf in to_fields]        
        if not set(connect_dict.values()) <= set(to_names):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS of ToComponent')

        if connect_dict:
            frominstance = FromComponent.attributes['NAME']
            toinstance = ToComponent.attributes['NAME']

            if isinstance(FromComponent, MappletIO): # mapplet output
                assert FromComponent.io_type.lower() == 'output', \
                        'Mapplet-input cannot be parent of other transformations in mapping.'
                parent = FromComponent.parent_mapplet
                frominstance = parent.name
                frominstancetype = 'Mapplet'
            else:
                frominstancetype = FromComponent._type

            if isinstance(ToComponent, MappletIO): # mapplet input
                assert ToComponent.io_type.lower() == 'input', \
                        'Mapplet-output cannot be child of other transformations in mapping.'
                parent = ToComponent.parent_mapplet
                toinstance = parent.name
                toinstancetype = 'Mapplet'
            else:
                toinstancetype = ToComponent._type
                

            # END Mapplet special attention
            for key, val in connect_dict.items():
                connection = {
                    'FROMFIELD': key,
                    'TOFIELD': val,
                    'FROMINSTANCE': frominstance,
                    'TOINSTANCE': toinstance,
                    'FROMINSTANCETYPE': frominstancetype,
                    'TOINSTANCETYPE': toinstancetype
                }
                self.connection_list.append(connection)

            # Declare children and parents
            if ToComponent not in FromComponent.children:
                FromComponent.children.append(ToComponent)
            if FromComponent not in ToComponent.parents:
                ToComponent.parents.append(FromComponent)


class MappletIO(Component):
    '''
    Represents the IO Transformations that Mapplets can contain
    '''
    def __init__(self, name, io_type, parent_mapplet):
        assert isinstance(io_type, str), 'Expected type str, was {}'.format(type(io_type))
        assert io_type.lower() in ['input', 'output'], 'io_type must be either \'input\' or \'output\''
        self.io_type = io_type.lower()

        valid_field_attribute_names = [
            'DATATYPE', 'DEFAULTVALUE', 'DESCRIPTION',
            'NAME', 'PICTURETEXT', 'PORTTYPE', 'PRECISION', 'SCALE'
        ]      

        if self.io_type.lower() == 'input':
            super().__init__(name=name, component_type='TRANSFORMATION')
            self.attributes = {
                'DESCRIPTION': 'Mapplet made with pypwc (contact SBS for more information)',
                'NAME': self.name,
                'OBJECTVERSION': '1',
                'REUSABLE': 'NO',
                'TYPE': 'Input Transformation',
                'VERSIONNUMBER': '1'
            }
            self.valid_field_attribute_names = valid_field_attribute_names
        if self.io_type.lower() == 'output':
            super().__init__(name=name, component_type='TRANSFORMATION')
            self.attributes = {
                'DESCRIPTION': 'Mapplet made with pypwc (contact SBS for more information)',
                'NAME': self.name,
                'OBJECTVERSION': '1',
                'REUSABLE': 'NO',
                'TYPE': 'Output Transformation',
                'VERSIONNUMBER': '1'
            }
            self.valid_field_attribute_names = valid_field_attribute_names
            

        assert isinstance(parent_mapplet, Mapplet), 'Parent must be Mapplet'
        self.parent_mapplet = parent_mapplet

class Mapplet(Composite):
    '''Represents a PowerCenter Mapplet transformation'''
    def __init__(self, name, component_list=None, connection_list=None):
        super().__init__(name, component_type='Mapplet',
                         component_list=component_list,
                         connection_list=connection_list)


        self.attributes = {
            'DESCRIPTION': 'Mapplet made with pypwc (contact SBS for more information)',
            'NAME': self.name,
            'OBJECTVERSION': '1',
            'REUSABLE': 'YES',
            'TYPE': 'Mapplet',
            'VERSIONNUMBER': '1'
        }



    @Composite.component_list.getter
    def component_list(self):
        if not self.input and not self.output:
            # print('only component_list')
            return self._component_list
        elif self.input and not self.output:
            # print('component_list and input')
            return self._component_list + list(self.input.values())
        elif not self.input and self.output:
            # print('component_list and output')
            return self._component_list + list(self.output.values())
        else:
            # print('component_list and input and output')
            # print(self.output)
            # print(self.input)
            return self._component_list + list(self.input.values()) + list(self.output.values())

    @property
    def _input_transformation_fields(self):
        input_fields = []
        for input in self.input.values():
            for input_field in input.fields:
                input_field = deepcopy(input_field)
                i_f = input_field[1]
                i_f.update({
                    'MAPPLETGROUP': input.name,
                    'PORTTYPE': 'INPUT',
                    'REF_FIELD': i_f['NAME'],
                    'REF_INSTANCETYPE': 'Input Transformation'
                })

                input_fields.append(input_field)
        return input_fields

    @property
    def _output_transformation_fields(self):
        output_fields = []
        for output in self.output.values():
            for output_field in output.fields:
                output_field = deepcopy(output_field)
                o_f = output_field[1]
                o_f.update({
                    'MAPPLETGROUP': output.name,
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


        InstanceTransformation = Component('{0}{1}'.format(self.name, Component._counter),
                                            component_type='TRANSFORMATION')
        Component._counter += 1
        InstanceTransformation.fields = self._input_transformation_fields + self._output_transformation_fields

        InstanceTransformation.attributes = self.attributes
        InstanceTransformation.table_attributes = {
            'Is Active': 'YES',
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




