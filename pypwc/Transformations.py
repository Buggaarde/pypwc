from abc import ABCMeta, abstractmethod
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom
from copy import deepcopy

from .Canvas import Component
from .fields import ofield

__author__ = 'Simon Bugge Siggaard'
__email__ = 'sbs@bec.dk'

class Transformation(Component, metaclass=ABCMeta):
    '''Any class inheriting from Transformation will need to define
    the setter of the name attribute'''
    def __init__(self, *, type, name=None, description=None,
                     object_version=None, reusable=None,
                     version_number=''):
        if type is None:
            self._type = ''
        else:
            assert isinstance(type, str)
            self._type = type
        
        if name is None:
            self._name = ''
        else:
            assert isinstance(name, str)
            self._name = name
        
        if description is None:
            self._description = ''
        else:
            assert isinstance(description, str)
            self._description = description

        if object_version is None:
            self._object_version = ''
        else:
            assert isinstance(object_version, str)
            self._object_version = object_version

        if reusable is None:
            self._reusable = ''
        else:
            assert isinstance(reusable, str)
            self._reusable = reusable
        
        if version_number is None:
            self._version_number = ''
        else:
            assert isinstance(version_number, str)
            self._version_number = version_number
        
        super().__init__(name=name, component_type='TRANSFORMATION')
        self.fields = []
        self.table_attributes = {'Tracing Level': 'Normal'}

        # Transformations have inputs and outputs that return themselves
        # so that it is possible to chain together composites with
        # transformations
        self.input = {'input': self}
        self.output = {'output': self}


    ## Begin properties section
    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, type):
        print('self.type cannot be changed from {}'.format(self.type))


    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        return self._set_name(value)

    @abstractmethod
    def _set_name(self, value):
        pass


    @property
    def description(self):
        return self._description

    @description.setter   
    def description(self, value):
        self._description = value
 

    @property
    def object_version(self):
        return self._object_version

    @object_version.setter
    def object_version(self, value):
        pass    


    @property      
    def reusable(self):
        return self._reusable

    @reusable.setter
    def reusable(self, value):   
        if value.upper() not in ('YES', 'NO'):
                raise ValueError('Property reusable must be either YES or NO. Attempted: "{}"'.format(value))
        else:
            self._reusable = value.upper()


    @property    
    def version_number(self):
        return self._version_number

    @version_number.setter    
    def version_number(self, value):
        self._version_number = value

    @property
    def attributes(self):
        return {
            'DESCRIPTION' : self._description,
            'NAME': self._name,
            'OBJECTVERSION': self.object_version,
            'REUSABLE': self.is_reusable,
            'TYPE': self._type,
            'VERSIONNUMBER': self.version_number
        }

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
    ## End properties section

    ## Begin methods section



class Expression(Transformation):
    '''Docs'''
    def __init__(self, name='EXP', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Expression',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
            
        self.valid_field_attribute_names = [
            'DATATYPE', 'DEFAULTVALUE', 'DESCRIPTION',
            'EXPRESSION', 'EXPRESSIONTYPE', 
            'NAME', 'PICTURETEXT', 'PORTTYPE', 'PRECISION', 'SCALE'
        ]

    def _set_name(self, value):
        if not value.upper().startswith('EXP'):
            self._name = 'EXP_{}'.format(value)
        else:
            self._name = value

    

class SourceQualifier(Transformation):
    '''Docs'''
    def __init__(self, name='SQ', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Source Qualifier',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('SQ'):
            self._name = 'SQ_{}'.format(value)
        else:
            self._name = value

class UpdateStrategy(Transformation):
    '''Docs'''
    def __init__(self, name='UPD', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Update Strategy',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('UPD'):
            self._name = 'UPD_{}'.format(value)
        else:
            self._name = value

class Filter(Transformation):
    '''Docs'''
    def __init__(self, name='FIL', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Filter',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('FIL'):
            self._name = 'FIL_{}'.format(value)
        else:
            self._name = value

class Aggregator(Transformation):
    '''Docs'''
    def __init__(self, name='AGG', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Aggregator',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)

        self.valid_field_attribute_names = [
            'DATATYPE', 'DEFAULTVALUE', 'DESCRIPTION', 'EXPRESSION',
            'EXPRESSIONTYPE', 'NAME', 'PICTURETEXT', 'PORTTYPE', 
            'PRECISION', 'SCALE'
        ]

        self.table_attributes = {
            'Cache Directory': '$PMCacheDir',
            'Tracing Level': 'Normal',
            'Sorted Input': 'YES',
            'Aggregator Data Cache Size': 'Auto',
            'Aggregator Index Cache Size': 'Auto',
            'Transformation Scope': 'All Input'
        }

    def _set_name(self, value):
        if not value.upper().startswith('AGG'):
            self._name = 'AGG_{}'.format(value)
        else:
            self._name = value
        
class Lookup(Transformation):
    '''Docs'''
    def __init__(self, name='LKP', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Lookup',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('LKP'):
            self._name = 'LKP_{}'.format(value)
        else:
            self._name = value

class Sequence(Transformation):
    '''Docs'''
    def __init__(self, name='SEQ',
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Sequence',
                             name=name,
                             description=None,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)

        self.valid_field_attribute_names = [
            'DATATYPE', 'DEFAULTVALUE', 'DESCRIPTION',
            'NAME', 'PICTURETEXT', 'PORTTYPE', 'PRECISION', 'SCALE'
        ]
            
        self.table_attributes = {
            'Start Value': '0',
            'Increment By': '1',
            'End Value': '9223372036854775807',
            'Current Value': '1',
            'Cycle': 'NO',
            'Number of Cached Values': '0',
            'Reset': 'YES',
            'Is Current Value Shared': 'NO',
            'Tracing Level': 'Normal'
        }

        self.add_fields([
            ofield(name='NEXTVAL', datatype='bigint', default_value="ERROR('transformation error')"),
            ofield('CURRVAL', 'bigint', default_value="ERROR('transformation error')")
        ])
        
    def _set_name(self, value):
        if not value.upper().startswith('SEQ'):
            self._name = 'SEQ_{}'.format(value)
        else:
            self._name = value

    @property
    def attributes(self):
        return {
            'NAME': self._name,
            'OBJECTVERSION': self.object_version,
            'REUSABLE': self.is_reusable,
            'TYPE': self._type,
            'VERSIONNUMBER': self.version_number
        }

    def as_instance(self):
        att = self.attributes
        attribute_dict = {
            'NAME': '' if not att['NAME'] else att['NAME'],
            'REUSABLE': '' if not att['REUSABLE'] else att['REUSABLE'],
            'TRANSFORMATION_NAME': '' if not att['NAME'] else att['NAME'],
            'TRANSFORMATION_TYPE': '' if not att['TYPE'] else att['TYPE'],
            'TYPE': '' if not self.component_type else self.component_type
        }
        root = ET.Element('INSTANCE', attrib=attribute_dict)
        return ET.ElementTree(root)
    


class Joiner(Transformation):
    '''Docs'''
    def __init__(self, name='JNR', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Joiner',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
        self._join_condition = ''
        self._join_type = ''

        self.valid_field_attribute_names = [
            'DATATYPE', 'DEFAULTVALUE', 'DESCRIPTION', 'NAME',
            'PICTURETEXT', 'PORTTYPE', 'PRECISION', 'SCALE'
        ]      

        self.table_attributes = {
            'Case Sensitive String Comparison': 'YES',
            'Cache Directory': '$PMCacheDir',
            'Join Condition': '',
            'Join Type': 'Normal Join',
            'Null ordering in master': 'Null Is Highest Value',
            'Null ordering in detail': 'Null Is Highest Value',
            'Tracing Level': 'Normal',
            'Joiner Data Cache Size': 'Auto',
            'Joiner Index Cache Size': 'Auto',
            'Sorted Input': 'YES',
            'Master Sort Order': 'Auto',
            'Transformation Scope': 'All Input'
        }


    @property
    def join_condition(self):
        return self._join_condition
    
    @join_condition.setter
    def join_condition(self, value):
        assert isinstance(value, str), 'Expected a str; was {}'.format(type(value))
        self._join_condition = value
        self.table_attributes['Join Condition'] = self._join_condition

    @property
    def join_type(self):
        return self._join_type
    
    @join_type.setter
    def join_type(self, value):
        assert isinstance(value, str), 'Expected a str; was {}'.format(type(value))
        self._join_type = value.title()
        self.table_attributes['Join Type'] = self._join_type
    


    def _set_name(self, value):
        if not value.upper().startswith('JNR'):
            self._name = 'JNR_{}'.format(value)
        else:
            self._name = value

class Normalizer(Transformation):
    '''Docs'''
    def __init__(self, name='NRM', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Normalizer',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('NRM'):
            self._name = 'NRM_{}'.format(value)
        else:
            self._name = value

class Rank(Transformation):
    '''Docs'''
    def __init__(self, name='RNK', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Rank',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('RNK'):
            self._name = 'RNK_{}'.format(value)
        else:
            self._name = value

class Router(Transformation):
    '''Represents the Router transformation.
    
    >>> rtr = pwc.Router(name='rtr_test')
    ... rtr.add_fields([
    ...     pwc.ifield('test1', 'integer'),    
    ...     pwc.ifield('test2', 'nstring')    
    ... ])
    ...
    ... rtr.add_group('Valid', condition="test1='1'")
    ... mplt.connect(exp_in, rtr, connect_dict={'test_int':'test1', 'test_nstring':'test2'})
    ... mplt.connect(rtr.group('Valid'), exp_out, connect_dict={'test2': 'test_output'})
    '''
    def __init__(self, name='RTR', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Router',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)

        self.valid_field_attribute_names = [
            'DATATYPE', 'DEFAULTVALUE', 'DESCRIPTION', 'GROUP',
            'NAME', 'PICTURETEXT', 'PORTTYPE', 'PRECISION', 'SCALE'
        ]

        # self.groups = {group_name: (group_description, group_condition, group_index, group_type), ...}
        self.groups = {}

    def _set_name(self, value):
        if not value.upper().startswith('RTR'):
            self._name = 'RTR_{}'.format(value)
        else:
            self._name = value

    def group(self, group_name):
        '''Returns a copy of the parent router, but all input and output fields
        have their names adjusted by the group index of the group_name.'''
        router_group = deepcopy(self)
        for field in router_group.get_all_ifields():
            # Add reference field to the router field
            field[1]['REF_FIELD'] = field[1]['NAME']
            # Add the group index to the name, based on the the group_name
            field[1]['NAME'] += self.groups[group_name][2]
            # Make the field belong to the correct group
            field[1]['GROUP'] = group_name
            # Make the field an output field
            field[1]['PORTTYPE'] = 'OUTPUT'

        return router_group




    


class Sorter(Transformation):
    '''Docs'''
    def __init__(self, name='SRT', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Sorter',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
     
        self.valid_field_attribute_names = [
            'DATATYPE', 'DEFAULTVALUE', 'DESCRIPTION',
            'ISSORTKEY', 'SORTDIRECTION',
            'EXPRESSION', 'EXPRESSIONTYPE', 
            'NAME', 'PICTURETEXT', 'PORTTYPE', 'PRECISION', 'SCALE'
        ]

        self.table_attributes = {
            'Sorter Cache Size': '1GB',
            'Case Sensitive': 'YES',
            'Work Directory': '$PMTempDir',
            'Distinct': 'NO',
            'Null Treated Low': 'NO',
            'Tracing Level': 'Normal',
            'Merge Only': 'NO',
            'Partitioning': 'Order records for individual partitions',
            'Transformation Scope': 'Transaction'
        }


    def _set_name(self, value):
        if not value.upper().startswith('SRT'):
            self._name = 'SRT_{}'.format(value)
        else:
            self._name = value

class TransactionControl(Transformation):
    '''Docs'''
    def __init__(self, name='TCT', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Transaction Control',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)

        self.valid_field_attribute_names = [
            'DATATYPE', 'DEFAULTVALUE', 'DESCRIPTION',
            'NAME', 'PICTURETEXT', 'PORTTYPE', 'PRECISION', 'SCALE'
        ]

        self.table_attributes = {
            'Tracing Level': 'Normal'
        }

    def _set_name(self, value):
        if not value.upper().startswith('TCT'):
            self._name = 'TCT_{}'.format(value)
        else:
            self._name = value


class Target(Transformation):
    '''Docs'''
    def __init__(self, name='TRG', description=None,
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Target Definition',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)

        self.component_type = 'TARGET'
        self.business_name = ''
        self.constraint = ''
        self.database_type = 'Netezza'
        self.table_options = ''
        self._load_order = ''

        self.table_attributes = {}

        self.valid_field_attribute_names = [
            'BUSINESSNAME', 'DATATYPE', 'DESCRIPTION',
            'FIELDNUMBER', 'KEYTYPE', 'NAME',
            'NULLABLE', 'PICTURETEXT', 'PRECISION', 'SCALE'
        ]



    def _set_name(self, value):
        self._name = value

    @property
    def attributes(self):
        return {
            'BUSINESSNAME': self.business_name,
            'CONSTRAINT' : self.constraint,
            'DATABASETYPE': self.database_type,
            'DESCRIPTION': self._description,
            'NAME': self.name,
            'OBJECTVERSION': self.object_version,
            'TABLEOPTIONS': self.table_options,
            'VERSIONNUMBER': self.version_number
        }


    def as_instance(self):
        # This differs by adding table attributes to the instance
        att = self.attributes
        attribute_dict = {
            'DESCRIPTION': '' if not att['DESCRIPTION'] else att['DESCRIPTION'],
            'NAME': '' if not att['NAME'] else att['NAME'],
            'TRANSFORMATION_NAME': '' if not att['NAME'] else att['NAME'],
            'TRANSFORMATION_TYPE': '' if not self.type else self.type,
            'TYPE': '' if not self.component_type else self.component_type
        }
        root = ET.Element('INSTANCE', attrib=attribute_dict)
        for name, value in self.table_attributes.items():
            ET.SubElement(root, 'TABLEATTRIBUTE', attrib={
                'NAME': name, 'VALUE': value    
            })
        return ET.ElementTree(root)

    def as_xml(self):
        '''Returns an ElementTree with the apppropriate children
        and attributes.'''
        # This differs by removing table_attributes from the fields
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

    @property
    def load_order(self):
        pass
    
    @load_order.setter
    def load_order(self, value):
        msg = 'load_order must be able to be interpreted as an int'
        assert isinstance(value, str) or isinstance(value, int), msg
        if isinstance(value, str):
            assert value.isdigit(), msg

        self._load_order = str(value)

    @load_order.getter
    def load_order(self):
        root = ET.Element('TARGETLOADORDER', attrib={
            'ORDER': self._load_order,
            'TARGETINSTANCE': self.name
        })
        return ET.ElementTree(root)
