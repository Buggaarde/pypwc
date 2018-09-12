from .pypwc.Canvas import Mapping, Mapplet, MappletIO, Component, Composite
from copy import deepcopy
from itertools import zip_longest

__author__ = 'Simon Bugge Siggaard'
__email__ = 'sbs@bec.dk'

def chain(composite_class, *, name, list_of_components):
    '''
    Connects together adjacent connectible components.
    This assumes that the output of one component is directly compatible with
    the input of the adjacent component.

    If nothing else is specified, it is assumed that all components have only
    a single input transformation and a single output transformation.

    Input/output transformations must be  specified, if Components have more 
    that a single input or output Transformation. This is done with the
    following syntax:

    >>> (multiple_io_component, 'input1', 'output3')
    
    where the first string indicates the name of the input and the second
    string indicates the name of the output port. If the Component has
    only a single input/output, an empty string can be used to specify
    this. E.g:

    >>> (multiple_output_component, '', 'output3')

    The composite_class uses connect_by_index to connect adjacent
    transformations, meaning that connections are formed one by one, until
    either of the transformations do not have more transformfields.

    Parameters:
    -----------
    composite_class: a valid Composite class
        Valid classes include any that bahave as a Composite class.
        Examples are Mapping, Mapplet and Composite.

    list_of_components: a list of components
        Every component in the list must have a .input and a .output
        dictionary containing the respective input and output transformations
        in the component.

    Returns:
    --------
    An object specified by the composite_class parameter.
    If Mapping (Mapplet), the result of chain will be a mapping (mapplet)
    with transformations connected appropriately inside. If Composite, the
    result will be a 'pseudo-mapplet' that in all ways behaves as a
    mapplet, except that it will only embed its components into parent
    composites, and not itself.

    Examples:
    --------
    Create a simple chain of functionality, without any branches.

    >>> m_ = chain(pwc.Mapping, [
    ...         source,
    ...         extract_flatfile_data,
    ...         eliminate_invalid_input,
    ...         if_newer_transaction_time,
    ...         if_different_MD5_checksum,
    ...         lookup_MODPART_I,
    ...         target
    ...     ])

    Create a branching chain, with two different targets.

    >>> chain1 = chain(pwc.Component, [
    ...         source,
    ...         (extract_valid_input, '', 'invalid'),
    ...         error_target   
    ...     ])
    ... chain2 = chain(pwc.Component, [
    ...         source,
    ...         (extract_valid_input, '', 'valid'),
    ...         target
    ...     ])
    ... m_ = Mapping('Branching', component_list=[chain1, chain2])
    '''
    # Type checking
    assert isinstance(list_of_components, list), 'list_of_components must be a list; was {}'.format(type(list_of_components))
    for component in list_of_components:
        assert (isinstance(component, Component) or isinstance(component, tuple))
        if isinstance(component, tuple):
            actual_component, input_name, output_name = component
            assert isinstance(actual_component, Component)
            assert isinstance(input_name, str)
            assert isinstance(output_name, str)
            assert hasattr(actual_component, 'input')
            assert hasattr(actual_component, 'output')
            assert isinstance(actual_component.input, dict), 'input must be a dict, was {}'.format(type(actual_component.input))
            assert isinstance(actual_component.output, dict), 'output must be a dict, was {}'.format(type(actual_component.output))
            if output_name:
                assert output_name in actual_component.output
            if input_name:
                assert input_name in actual_component.input
        else:
            assert hasattr(component, 'input')
            assert hasattr(component, 'output')
            assert isinstance(component.input, dict), 'input must be a dict, was {}'.format(type(component.input))
            assert isinstance(component.output, dict), 'output must be a dict, was {}'.format(type(component.output))

    chain_pairs = zip(list_of_components[:-1], list_of_components[1:])
    output_composite = composite_class(name)
    for (left_specifier, right_specifier) in chain_pairs:
        if isinstance(left_specifier, tuple):
            left, _, output_name = left_specifier
            if not output_name:
                assert len(left.output) == 1, 'Found more than one output-name; when no name is specified, it is assumed that there is only a single output.'
                output_name = list(left.output.keys())[0]
        elif isinstance(left_specifier, Component):
            left = left_specifier
            assert len(left.output) == 1
            output_name = list(left.output.keys())[0]         
        if isinstance(right_specifier, tuple):
            right, input_name, _ = right_specifier
            if not input_name: 
                assert len(right.input) == 1, 'Found more than one input-name; when no name is specified, it is assumed that there is only a single input.'
                input_name = list(right.input.keys())[0]
        elif isinstance(right_specifier, Component):
            right = right_specifier
            assert len(right.input) == 1
            input_name = list(right.input.keys())[0]

        output_composite.add_components([left, right])

        # Assumes that the two Components can be connected by index
        output_composite.connect_by_index(
            left.output[output_name], right.input[input_name]
            )

    return output_composite



def map_transformation_to_fields(transformation, input_transformation,
                                 constant_connections={}, default_connection='datatype'):
    assert isinstance(constant_connections, dict)
    assert isinstance(default_connection, str)
    assert default_connection.lower() in ['datatype', 'name']

    transformation_name = transformation.name
    input_transform = deepcopy(input_transformation)
    mplt = Mapplet(name='mplt_map_transformation_to_inputs',
                    component_list=[input_transform])

    for _, field in input_transform.get_all_transformfields():
        transform = deepcopy(transformation)
        transform.name += '_{}'.format(field['NAME'])
        mplt.add_component(transform)
        input_field_datatype = field['DATATYPE']
        if default_connection == 'datatype':
            transformfields = transform.get_all_transformfields()
            field_with_input_datatype = [
                t['NAME'] for (_, t) in transformfields
                if t['DATATYPE'] == input_field_datatype
                ]
            assert len(field_with_input_datatype) == 1, \
                    'Found more than one field in {} with datatype {}'.format(
                        transformation_name, input_field_datatype)
            new_connections = {field['NAME']: field_with_input_datatype[0]}
            new_connections.update(constant_connections)

            mplt.connect(input_transform, transform,
                        connect_dict=new_connections)
        elif default_connection == 'name':
            pass

    return mplt

def grouper(iterable, n, fillvalue=None):
    '''Collect data into fixed-length chunks or blocks

    >>> grouper('ABCDEFG', 3, 'x')
    ABC DEF Gxx
    '''
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)

def map(applied_transformation, input_transformation,
        constant_connections={}, mode='index',
        return_composite=Composite):
    '''
    Applies applied_transformation to the fields of input_transformation,
    roughly the same way map() normally works.

    The number of fields in input_transformation connected to each
    applied_transformation, is equal to the number of input fields in 
    applied_transformation _minus_ the number of constant_connections.
    The fields are grouped in order from the top, not including any
    fields specified in constant_connections.

    Assumes that fields are connection compatible.

    Parameters:
    -----------
    applied_transformation: a valid Transformation
        A transformation (usually an Expression),

    input_transformation: a valid Transformation

    constant_connections: dict (optional, default: {})

    mode: string (optional, default: 'index')
        Tells the function in which way the applied transformation should
        connect to the input_transformation.
        Allowed values are: 'index', 'name' and 'type'.

        Currently, only 'index' is implemented.


    return_composite: a valid Composite object (optional, default: Composite)

    Returns:
    --------
    A Composite object of the same type as return_composite

    Raises:
    -------
    Raises an AssertionError if the number of input fields is not
    compatible with the number of non-constant fields in applied_transformation

    Examples:
    ---------
    A simple example is the following: Assuming that applied_trans contains
    a single iofield, that performs the desired transformation, and that
    input_trans contains 10 output fields, then

    >>> mapped_composite = pwc.functional.map(applied_trans, input_trans)

    returns a Composite object with a single input transformation and 10
    copies of applied_trans, with all 10 output fields in input_trans
    connection to their own copy.


    Let's say that the input_transformation now also contains some input data
    and an input line that will be an input in each applied_trans. For 
    the sake of the example, let us also say that applied_trans now have
    three fields, 'a_const_input1', 'a_const_input2' and the transformation
    field from the previous example. This relationship can be expressed via
    the constant_connection argument, like below:

    >>> mapped_composite = pwc.functional.map(applied_trans, input_trans,
    ...                             constant_connections={
    ...                                 'a_const_input1': 'i_input_line',
    ...                                 'a_const_input2': 'i_input_data'    
    ...                                 }
    
    '''
    comp = return_composite(name='map')
    comp.add_component(input_transformation)
    if mode == 'index':
        n_fields_applied = len(applied_transformation.get_all_transformfields())
        n_fields_input = len(input_transformation.get_all_transformfields())
        num_non_constant_applied = n_fields_applied - len(constant_connections)
        num_non_constant_input = n_fields_input - len(constant_connections)
        assert num_non_constant_input % num_non_constant_applied == 0, 'The number of non-constant_connection fields in input_transformation ({0}) is not divisible by the number of non-constant_connection fields in applied_transformation ({1}).'.format(num_non_constant_input, num_non_constant_applied)
        num_sets_of_input_fields = int(num_non_constant_input/num_non_constant_applied)

        groups_of_input = grouper(filter(lambda x: x not in constant_connections.values(),
                                     input_transformation.get_all_transformfield_names()),
                                     num_non_constant_applied)
        non_constant_field_names_applied = filter(lambda x: x not in constant_connections,
                                    applied_transformation.get_all_transformfield_names())
        for idx, group in enumerate(groups_of_input):
            new_applied_transformation = deepcopy(applied_transformation)
            new_applied_transformation.name += '{}'.format(idx)
            comp.add_component(new_applied_transformation)
            comp.connect(input_transformation, new_applied_transformation, connect_dict=constant_connections)
            comp.connect(input_transformation, new_applied_transformation, 
                            connect_dict=dict(zip(group, non_constant_field_names_applied)))

    elif mode == 'name':
        raise NotImplementedError
    elif mode == 'type':
        raise NotImplementedError


if __name__ == '__main__':
    from pypwc.fields import *
    from pypwc.Transformations import Expression

    number_of_expressions = 35
    number_of_mapplets = 15

    mapplets = []
    for num_mplt in range(number_of_mapplets):
        expressions = []
        for exp in range(number_of_expressions):
            iofields = [
                iofield('{}field1'.format(exp), 'bigint'),
                iofield('{}field2'.format(exp), 'integer'),
                iofield('{}field3'.format(exp), 'nstring'),
                iofield('{}field4'.format(exp), 'string')
            ]
            expression = Expression(name='exp_{}'.format(exp))
            expression.add_fields(iofields)
            expressions.append(expression)

        comp = chain(Composite, name='default_composite', 
                    list_of_components=expressions)

        mplt = Mapplet(name='test_mapplet{}'.format(num_mplt), component_list=[comp])
        
        mplt_ifields = [
            ofield('{}i1'.format(num_mplt), 'bigint'),
            ofield('{}i2'.format(num_mplt), 'integer'),
            ofield('{}i3'.format(num_mplt), 'nstring'),
            ofield('{}i4'.format(num_mplt), 'string')
        ]

        mplt_ofields = [
            ifield('{}o1'.format(num_mplt), 'bigint'),
            ifield('{}o2'.format(num_mplt), 'integer'),
            ifield('{}o3'.format(num_mplt), 'nstring'),
            ifield('{}o4'.format(num_mplt), 'string')
        ]

        mplt.input['input'] = MappletIO(name='INPUT', io_type='input', parent_mapplet=mplt)
        mplt.input['input'].add_fields(mplt_ifields)
        mplt.output['output'] = MappletIO(name='OUTPUT', io_type='output', parent_mapplet=mplt)
        mplt.output['output'].add_fields(mplt_ofields)

        mplt.connect_by_index(mplt.input['input'], mplt.component_list[0])
        mplt.connect_by_index(mplt.component_list[34], mplt.output['output'])

        mapplets.append(mplt)

    m_ = chain(Mapping, name='default_mapping', list_of_components=mapplets)
    m_.write(r'./m_test.xml')