from abc import ABCMeta, abstractmethod
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom

class Component(object):
    '''Anything that resides in a canvas should be a component
    and any combination of components should themselves be components.
    
    Implements the composite design pattern.'''
    _names = []
    _allowed_types = ['SOURCE', 'TARGET', 'EXPRMACRO',
                        'TRANSFORMATION', 'MAPPLET', 'MAPPING',
                        'FOLDER', 'REPOSITORY', 'POWERMART']
    def __init__(self,*, name, component_type, component_list=[]):
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

        assert isinstance(component_list, list)
        if component_list:
            self.is_composite = True
        self.component_list = component_list

    @property
    def is_composite(self):
        return self._is_composite

    @is_composite.setter
    def is_composite(self, value):
        assert isinstance(value, bool)
        if value == True:
            if fields:
                raise ValueError('It makes no sense for composite components to have fields. Found the following fields:\n{}'.format(self.fields))
            elif attributes:
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
            self.fields += field

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
        if not set(connect_dict.vals()) <= set(other_fields):
            raise ValueError('There are fields in connect_dict that are not contained in the set of TRANSFORMFIELDS')

        # Declare children and parents
        self.children.append(OtherComponent)
        OtherComponent.parents.append(self)

        # Construct a new Component with the composite data, and return
        CompositeComponent = Component()
        CompositeComponent.is_composite = True
        CompositeComponent.component_list.append(self)
        CompositeComponent.component_list.append(OtherComponent)
        CompositeComponent.connections.append(
                (self, OtherComponent, connect_dict)
            )

        return CompositeComponent



    def _add_subelements_to_root_not_composite(self, root, fields):
        for f in fields:
            assert (len(f) == 2 or len(f) == 3)
            if len(f) == 2: # No nested fields
                fieldtype, attrib_dict = f
                ET.SubElement(root, fieldtype, attrib=attrib_dict)
            elif len(f) == 3: # Yes nested fields
                fieldtype, attrib_dict, nested_fields = f
                local_root = ET.Element(fieldtype, attrib=attrib_dict)
                self._add_subelements_to_root_not_composite(local_root, nested_fields)
                root.append(local_root)


    def as_xml(self):
        '''Returns an ElementTree with the apppropriate children
        and attributes'''
        if not self.is_composite:
            root = ET.Element(self.component_type, attrib=self.attributes)
            self._add_subelements_to_root_not_composite(root, self.fields)
            TREE = ET.ElementTree(root)
            return TREE
        else:   # In the Component base class, the returned XML of composite
                # Components is wrapped in a <COMPOSITE /> tag. This behaviour
                # is assumed to be overwritten in components of type MAPPING
                # and MAPPLET.
            raise NotImplementedError('Not currently prioritized. As it stands right now, there is no real reason to handle the xml structure of composite Components.')


    def write(self, path):
        '''
        Reparse the one-lined default xml and write the prettified version to path.
        '''
        ugly_string = ET.tostring(self.as_xml().getroot())
        reparsed = minidom.parseString(ugly_string)
        with open(path, mode='w', encoding='utf8') as file:
            file.write(reparsed.toprettyxml(indent='    '))



class Canvas(Component, metaclass=ABCMeta):
    '''Docstring'''
    def __init__(component_list=[]):
        # component_list is a list of nestables that should be nested inside the canvas
        self.component_list = component_list


    

