from abc import ABCMeta, abstractmethod
import xml.etree.cElementTree as ET
import xml.dom.minidom as minidom

from Canvas import Component


class Transformation(Component, metaclass=ABCMeta):
    '''Any class inheriting from Transformation will need to define
    the setter of the name attribute'''
    def __init__(self, *, type, name='', description='',
                     object_version='', reusable='',
                     version_number=''):
        self._description = description
        self._name = name
        self._object_version = object_version
        self._reusable = reusable
        self._type = type
        self._version_number = version_number

        super().__init__(name=name, component_type='TRANSFORMATION')
        self.fields = []
        self.table_attributes = {'Tracing Level': 'Normal'}


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
    def __init__(self, name='EXP', description='',
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Expression',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
        
    def _set_name(self, value):
        if not value.upper().startswith('EXP'):
            self._name = 'EXP_{}'.format(value)
        else:
            self._name = value

class SourceQualifier(Transformation):
    '''Docs'''
    def __init__(self, name='SQ', description='',
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
    def __init__(self, name='UPD', description='',
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
    def __init__(self, name='FIL', description='',
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
    def __init__(self, name='AGG', description='',
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Aggregator',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('AGG'):
            self._name = 'AGG_{}'.format(value)
        else:
            self._name = value
        
class Lookup(Transformation):
    '''Docs'''
    def __init__(self, name='LKP', description='',
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
    def __init__(self, name='SEQ', description='',
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Sequence',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('SEQ'):
            self._name = 'SEQ_{}'.format(value)
        else:
            self._name = value

class Joiner(Transformation):
    '''Docs'''
    def __init__(self, name='JNR', description='',
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Joiner',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('JNR'):
            self._name = 'JNR_{}'.format(value)
        else:
            self._name = value

class Normalizer(Transformation):
    '''Docs'''
    def __init__(self, name='NRM', description='',
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
    def __init__(self, name='RNK', description='',
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
    '''Docs'''
    def __init__(self, name='RTR', description='',
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Router',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('RTR'):
            self._name = 'RTR_{}'.format(value)
        else:
            self._name = value

class Sorter(Transformation):
    '''Docs'''
    def __init__(self, name='SRT', description='',
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Sorter',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('SRT'):
            self._name = 'SRT_{}'.format(value)
        else:
            self._name = value

class TransactionControl(Transformation):
    '''Docs'''
    def __init__(self, name='TCT', description='',
                     object_version='1', reusable='NO',
                     version_number='1'):
        super().__init__(type='Transaction Control',
                             name=name,
                             description=description,
                             object_version=object_version,
                             reusable=reusable,
                             version_number=version_number)
        
    def _set_name(self, value):
        if not value.upper().startswith('TCT'):
            self._name = 'TCT_{}'.format(value)
        else:
            self._name = value
            
    