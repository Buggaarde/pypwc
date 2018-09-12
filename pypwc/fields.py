import re

'''
A module containing functions that generate TRANSFORMFIELDS
without the boilerplate.
'''

__author__ = 'Simon Bugge Siggaard'
__email__ = 'sbs@bec.dk'

static_precision_dict = {
    'bigint': '19',
    'date/time': '29',
    'double': '15',
    'integer': '10',
    'real': '7',
    'small integer': '5'
}

variable_precision_default_dict = {
    'binary': '5',
    'decimal': '29',
    'nstring': '10',
    'ntext': '10',
    'string': '5',
    'text': '5'
}

static_scale_dict = {
    'bigint': '0',
    'binary': '0',
    'date/time': '9',
    'double': '0',
    'integer': '0',
    'nstring': '0',
    'ntext': '0',
    'real': '0',
    'small integer': '0',
    'string': '0',
    'text': '0'
}

variable_scale_default_dict = {
    'decimal': '0'
}

def transformfield(*, porttype, name, datatype,
            default_value='', description='', expression='',
            expressiontype='', picture_text='', precision='',
            scale='', issortkey='', sortdirection='', master=False,
            group=''):

    # input validation
    assert isinstance(porttype, str), 'Expected str; was {}'.format(type(porttype))
    assert porttype.lower() in ['input', 'output', 'input/output', 'local variable'], \
            r"porttype must be either 'input', 'output', 'input/output' or 'local variable', was {}".format(porttype)
    assert isinstance(name, str), 'Expected str; was {}'.format(type(name))
    assert isinstance(datatype, str), 'Expected str; was {}'.format(type(datatype))
    allowed_datatypes = ['bigint', 'binary', 'date/time', 'decimal', 'double',
                        'integer', 'nstring', 'ntext', 'real', 'small integer',
                        'string', 'text']
    assert datatype in allowed_datatypes, 'Datatype must be in {}'.format(allowed_datatypes)
    assert isinstance(precision, str), 'Expected str; was {}'.format(type(precision))
    assert isinstance(scale, str), 'Expected str; was {}'.format(type(scale))
    assert not precision or precision.isdigit(), 'Precision must be a positive integer'
    assert not scale or scale.isdigit(), 'Scale must be a positive integer'
    assert isinstance(master, bool), 'Expected a bool; was {}'.format(type(master))
    assert isinstance(group, str), 'Group must be a str, was {}'.format(type(group))
                
    precision_is_static = datatype in static_precision_dict
    precision_is_variable = datatype in variable_precision_default_dict
    scale_is_static = datatype in static_scale_dict
    scale_is_variable = datatype in variable_scale_default_dict

    # Strip unnecessary whitespace from descriptions
    description = re.sub('\s+', ' ', description).strip()
    

    if precision_is_static:
        precision = static_precision_dict[datatype]
    elif not precision:
        precision = variable_precision_default_dict[datatype]
    if scale_is_static:
        scale = static_scale_dict[datatype]
    elif not scale:
        scale = variable_scale_default_dict[datatype]

    if porttype.lower() == 'input':
        expression = "{}".format(name)
    elif porttype.lower() == 'input/output':
        expression = "{}".format(name)

    if master:
        porttype += '/MASTER'

       
    field_dict = dict([
        ('DATATYPE', datatype),
        ('DEFAULTVALUE', default_value),
        ('DESCRIPTION', description),
        ('EXPRESSION', expression),
        ('EXPRESSIONTYPE', expressiontype),
        ('NAME', name),
        ('PICTURETEXT', picture_text),
        ('PORTTYPE', porttype),
        ('PRECISION', precision),
        ('SCALE', scale),
        ('ISSORTKEY', issortkey),
        ('SORTDIRECTION', sortdirection),
        ('GROUP', group)
    ])
   
    return ('TRANSFORMFIELD', field_dict)


def ifield(name, datatype,
           default_value='', description='', expression='',
           expressiontype='GENERAL', picture_text='', precision='',
           scale='', issortkey='NO', sortdirection='ASCENDING', master=False,
           group='INPUT'):
    return transformfield(porttype='INPUT', name=name, datatype=datatype,
                    default_value=default_value, description=description,
                    expression=expression, expressiontype=expressiontype,
                    picture_text=picture_text, precision=precision,
                    scale=scale, issortkey=issortkey, master=master,
                    sortdirection=sortdirection, group=group)

def ofield(name, datatype,
           default_value='', description='', expression='',
           expressiontype='GENERAL', picture_text='', precision='',
           scale='', issortkey='NO', sortdirection='ASCENDING', master=False,
           group='OUTPUT'):
    return transformfield(porttype='OUTPUT', name=name, datatype=datatype,
                    default_value=default_value, description=description,
                    expression=expression, expressiontype=expressiontype,
                    picture_text=picture_text, precision=precision,
                    scale=scale, issortkey=issortkey, master=master, 
                    sortdirection=sortdirection, group=group)

def iofield(name, datatype,
           default_value='', description='', expression='',
           expressiontype='GENERAL', picture_text='', precision='',
           scale='', issortkey='NO', sortdirection='ASCENDING', master=False,
           group='INPUT/OUTPUT'):
    return transformfield(porttype='INPUT/OUTPUT', name=name, datatype=datatype,
                    default_value=default_value, description=description,
                    expression=expression, expressiontype=expressiontype,
                    picture_text=picture_text, precision=precision,
                    scale=scale, issortkey=issortkey, master=master, 
                    sortdirection=sortdirection, group=group)

def vfield(name, datatype,
           default_value='', description='', expression='',
           expressiontype='GENERAL', picture_text='', precision='',
           scale='', issortkey='NO', sortdirection='ASCENDING', master=False,
           group='VARIABLE'):
    return transformfield(porttype='LOCAL VARIABLE', name=name, datatype=datatype,
                    default_value=default_value, description=description,
                    expression=expression, expressiontype=expressiontype,
                    picture_text=picture_text, precision=precision,
                    scale=scale, issortkey=issortkey, master=master, 
                    sortdirection=sortdirection, group=group)




def targetfield(name, datatype,
                businessname='', keytype='NOT A KEY', nullable='',
                description='', fieldnumber='', picture_text='',
                precision='', scale=''):

    # input validation
    assert isinstance(name, str), 'Expected str; was {}'.format(type(name))
    assert isinstance(datatype, str), 'Expected str; was {}'.format(type(datatype))
    assert isinstance(precision, str), 'Expected str; was {}'.format(type(precision))
    assert isinstance(scale, str), 'Expected str; was {}'.format(type(scale))
    assert not precision or precision.isdigit(), 'Precision must be a positive integer'
    assert not scale or scale.isdigit(), 'Scale must be a positive integer'

    # Strip unnecessary whitespace from descriptions
    description = re.sub('\s+', ' ', description).strip()

    field_dict = dict([
        ('BUSINESSNAME', businessname),
        ('DATATYPE', datatype),
        ('DESCRIPTION', description),
        ('FIELDNUMBER', fieldnumber),
        ('KEYTYPE', keytype),
        ('NAME', name),
        ('NULLABLE', nullable),
        ('PICTURETEXT', picture_text),
        ('PRECISION', precision),
        ('SCALE', scale),
    ])
   
    return ('TARGETFIELD', field_dict)

def name_of_field(field):
    return field[1]['NAME']


def mvar(name, datatype,
        aggfunction='',
        default_value='',
        description='',
        is_expressionvariable='NO',
        is_param='',
        precision='',
        scale='',
        userdefined='YES'
        ):



    assert isinstance(name, str), 'Expected str; was {}'.format(type(name))
    assert isinstance(datatype, str), 'Expected str; was {}'.format(type(datatype))
    allowed_datatypes = ['bigint', 'binary', 'date/time', 'decimal', 'double',
                        'integer', 'nstring', 'ntext', 'real', 'small integer',
                        'string', 'text']
    assert datatype in allowed_datatypes, 'Datatype must be in {}'.format(allowed_datatypes)
    assert isinstance(precision, str), 'Expected str; was {}'.format(type(precision))
    assert isinstance(scale, str), 'Expected str; was {}'.format(type(scale))
    assert not precision or precision.isdigit(), 'Precision must be a positive integer'
    assert not scale or scale.isdigit(), 'Scale must be a positive integer'
                
    precision_is_static = datatype in static_precision_dict
    precision_is_variable = datatype in variable_precision_default_dict
    scale_is_static = datatype in static_scale_dict
    scale_is_variable = datatype in variable_scale_default_dict
    
    if precision_is_static:
        precision = static_precision_dict[datatype]
    else:
        if not precision:
            precision = variable_precision_default_dict[datatype]
    if scale_is_static:
        scale = static_scale_dict[datatype]
    else:
        if not scale:
            scale = variable_scale_default_dict[datatype]
    
    if aggfunction:
        is_param = 'NO'
    else:
        is_param = 'YES'

    # Strip unnecessary whitespace from descriptions
    description = re.sub('\s+', ' ', description).strip()




    mvar = ('MAPPINGVARIABLE', {
            'NAME': name,
            'DATATYPE': datatype,
            'DEFAULTVALUE': default_value,
            'DESCRIPTION': description,
            'ISEXPRESSIONVARIABLE': is_expressionvariable, 
            'ISPARAM': is_param,
            'PRECISION': precision,
            'SCALE': scale,
            'USERDEFINED': userdefined
            })

    if not aggfunction:
        return mvar
    else:
        mvar[1]['AGGFUNCTION'] = aggfunction
        return mvar
