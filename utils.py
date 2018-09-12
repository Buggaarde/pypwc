import pytools
from .pypwc.fields import *
from .pypwc.Canvas import *
from .pypwc.Transformations import *
import DatabaseConnection as dbc

import decimal
import datetime
from copy import deepcopy

py_pwc_type_dict = {
    (int, 19): 'bigint',
    (int, 10): 'integer',
    (int, 3): 'small integer',
    (decimal.Decimal, 6): 'decimal',
    (str, 32): 'nstring',
    (str, 50): 'nstring',
    (str, 60): 'nstring',
    (datetime.datetime, 26): 'date/time'
}

py_nz_type_dict = {
    (int, 19): 'bigint',
    (int, 10): 'integer',
    (int, 3): 'byteint',
    (decimal.Decimal, 6): 'numeric',
    (str, 32): 'nvarchar',
    (str, 50): 'nvarchar',
    (str, 60): 'nvarchar',
    (datetime.datetime, 26): 'timestamp'
}

pwc_nz_type_dict = {
    'bigint': 'bigint',
    'integer': 'integer',
    'small integer': 'byteint',
    'decimal': 'numeric',
    'string': 'string',
    'nstring': 'nvarchar',
    'date/time': 'timestamp'
}

nz_pwc_type_dict = {val: key for key, val in pwc_nz_type_dict.items()}

def _name(description):
    return description[0]

def _type_code(description):
    return description[1]

def _display_size(description):
    return description[2]

def _internal_size(description):
    return description[3]

def _col_precision(description):
    return description[4]

def _scale(description):
    return description[5]

def _null_ok(description):
    return description[6]

def get_nz_datatype_from_description(description):
    '''Returns nvarchar if type is str.'''
    if _type_code(description) is str:
        return 'nvarchar'
    elif _type_code(description) is decimal.Decimal:
        return 'numeric'
    else:
        return py_nz_type_dict[(_type_code(description),
                             _internal_size(description))]

def get_pwc_datatype_from_description(description):
    return nz_pwc_type_dict[get_nz_datatype_from_description(description)]

def print_description(description):
    name, type_code, display_size, \
    internal_size, col_precision, \
    scale, null_ok = description
    print('Name: {}'.format(name))
    print('type_code: {}'.format(type_code))
    print('display_size: {}'.format(display_size))
    print('internal_size: {}'.format(internal_size))
    print('col_precision: {}'.format(col_precision))
    print('scale: {}'.format(scale))
    print('null_ok: {}'.format(null_ok))

def weave_two_lists(list1, list2):
    return [a for b in zip(list1, list2) for a in b]

def file_get_contents(filename):
    with open(filename) as f:
        return f.read()

def field_names_from_sql(sql, env='MDW'):
    '''
    Assumes that the sql return 2 columns. The first column
    is assumed to contain the name of the field, and the 2nd column
    is assumed to contain an nstring expression.
    '''
    # Connecting to the database
    host = 'NZDEV.RES.BEC.DK'
    database = 'DEV_{}'.format(env) # DEV because tables are always in DEV
    with dbc.DatabaseConnection(host=host, database=database) as db:
        db.sql = sql
        data, column_names, _ = db.sql_results
    assert len(column_names) == 2

    field_names = [d[0] for d in data]
    expressions = [d[1] for d in data]
    transformfields = [
        ofield(info[0],
                datatype='nstring',
                expression="'{}'".format(info[1]),
                precision='{}'.format(len(info[1])))
        for info in zip(field_names, expressions)]
    return transformfields

def target_from_sql(sql, env='MDW'):

    # Janky way to find name from sql:
    trg_name = sql.split(' ')[3]

    trg = Target(name=trg_name)

    # Connecting to the database
    host = 'NZDEV.RES.BEC.DK'
    database = 'DEV_{}'.format(env)
    with dbc.DatabaseConnection(host=host, database=database) as db:
        db.sql = sql
        _, column_names, descriptions = db.sql_results
        column_types = [d[1] for d in descriptions]

    # Converting datatypes from the DatabaseConnection to
    # useful types in both PowerCenter and Netezza
    nz_datatypes = map(get_nz_datatype_from_description, descriptions)
    nz_col_name_and_type = zip(descriptions, column_names, nz_datatypes)



    # Creating fields for the pwc.Target
    target_fields = [
        targetfield(name.upper(), datatype,
                    precision=str(_col_precision(description)),
                    scale=str(_scale(description)),
                    fieldnumber=str(i+1),
                    nullable='NULL' if _null_ok(description) else 'NOTNULL')
        for i, (description, name, datatype) in enumerate(nz_col_name_and_type)
        ]

    # Assume that (only) the first key in the table is the primary key
    target_fields[0][1]['KEYTYPE'] = 'PRIMARY KEY'
    trg.add_fields(target_fields)
    trg.load_order = '0'
    return trg

def source_from_sql(composite, sql):
    raise NotImplementedError

def _make_passthru_iofield_from_field(field):
    if field[0] == 'TARGETFIELD':
        datatype = nz_pwc_type_dict[field[1]['DATATYPE']]
    else:
        datatype = field[1]['DATATYPE']
        
    description = field[1]['DESCRIPTION']
    name = field[1]['NAME']
    picture_text = field[1]['PICTURETEXT']
    precision = field[1]['PRECISION']
    scale = field[1]['SCALE']

    io_field = iofield(name, datatype,
                        description=description, precision=precision,
                        picture_text=picture_text, scale=scale)

    return io_field

def _adjust_field_type_to_io(field):
    adj_field = deepcopy(field)
    adj_field[1]['PORTTYPE'] = 'INPUT/OUTPUT'
    adj_field[1]['GROUP'] = 'INPUT/OUTPUT'
    if 'EXPRESSION' in adj_field[1]:
        adj_field[1]['EXPRESSION'] = adj_field[1]['NAME']
    return adj_field

def passthru_from(component, component_type=Expression, name=None):
    if component.component_type == 'TARGET':
        raise ValueError("passthru's can only be connected TO targets, not from")

    if name:
        assert isinstance(name, str), 'name must be a string'
        given_name = name
    else:
        given_name = 'passthru_from_{}'.format(component.name)        
    passthru = component_type(name=given_name)
    component_fields = component.get_all_ofields()
    io_component_fields = map(_make_passthru_iofield_from_field, component_fields)
    passthru.add_fields(list(io_component_fields))

    return passthru

def passthru_to(component, component_type=Expression, name=None):
    if name:
        assert isinstance(name, str), 'name must be a string'
        given_name = name
    else:
        given_name = 'passthru_from_{}'.format(component.name)
     
    passthru = component_type(name=given_name)
    if component.component_type == 'TARGET':
        component_fields = component.get_all_fields_of_type('TARGETFIELD')
        io_component_fields = map(_make_passthru_iofield_from_field, component_fields)
        passthru.add_fields(list(io_component_fields))
    else:
        component_fields = component.get_all_ifields()
        io_component_fields = map(_make_passthru_iofield_from_field, component_fields)
        passthru.add_fields(list(io_component_fields))

    return passthru