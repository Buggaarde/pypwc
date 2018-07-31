from Transformations import Expression
from Canvas import Composite, Mapping, Mapplet
    
if __name__ == '__main__':
    Exp = Expression()
    # Exp.type = 'Aggregator'
    Exp.name = 'Test'
    Exp.reusable = 'no'
    field_dict = {
        'DATATYPE': 'bigint',
        'DEFAULTVALUE': '',
        'DESCRIPTION': '',
        'EXPRESSION': 'LINE_NR',
        'EXPRESSIONTYPE': 'GENERAL',
        'NAME': 'ANDEL_AF_LAAN_X',
        'PICTURETEXT': '',
        'PORTTYPE': 'INPUT/OUTPUT',
        'PRECISION': '19',
        'SCALE': '0'
        }
    fields = [
        ('TRANSFORMFIELD', field_dict)
    ]
    Exp.add_fields(fields)

    Exp.write(r'./Exp.xml')

    Exp1 = Expression(name='second')
    field_dict = {
        'DATATYPE': 'bigint',
        'DEFAULTVALUE': '',
        'DESCRIPTION': '',
        'EXPRESSION': 'LINE_NR',
        'EXPRESSIONTYPE': 'GENERAL',
        'NAME': 'LINE_NR',
        'PICTURETEXT': '',
        'PORTTYPE': 'INPUT/OUTPUT',
        'PRECISION': '19',
        'SCALE': '0'
        }
    fields1 = [
        ('TRANSFORMFIELD', field_dict)
    ]
    Exp1.add_fields(fields1)
    # print(Exp1.fields)
    Exp1.write(r'./Exp1.xml')


    component_list = [Exp, Exp1]
    Comp = Exp.connect_to(Exp1, {'ANDEL_AF_LAAN_X': 'LINE_NR'})
    Comp.write(r'./Comp.xml')

    Comp1 = Composite(name='Composite1')

    Map = Mapping(name='m_Map', component_list=component_list)#, connection_list=Comp.connection_list)
    Map.connect(Exp, Exp1, {'ANDEL_AF_LAAN_X': 'LINE_NR'})
    Map.write(r'./Map.xml')

    Mplt1 = Mapplet(name='mplt_test')
    
    Mplt = Mapplet(name='mplt_MAPPLET', component_list=component_list, connection_list=Comp.connection_list)
    input_fields = [('TRANSFORMFIELD', {
        'DATATYPE': 'bigint',
        'DEFAULTVALUE': '',
        'DESCRIPTION': '',
        'NAME': 'in_ANDEL_AF_LAAN_X',
        'PICTURETEXT': '',
        'PORTTYPE': 'OUTPUT',
        'PRECISION': '19',
        'SCALE': '0'
    })]
    Mplt.Input.add_fields(input_fields)
    output_fields = [('TRANSFORMFIELD', {
        'DATATYPE': 'bigint',
        'DEFAULTVALUE': '',
        'DESCRIPTION': '',
        'NAME': 'out_ANDEL_AF_LAAN_X',
        'PICTURETEXT': '',
        'PORTTYPE': 'INPUT',
        'PRECISION': '19',
        'SCALE': '0'
    })]
    Mplt.Output.add_fields(output_fields)
    Mplt.connect(Mplt.Input, Exp, {'in_ANDEL_AF_LAAN_X': 'ANDEL_AF_LAAN_X'})
    Mplt.connect(Exp1, Mplt.Output, {'LINE_NR': 'out_ANDEL_AF_LAAN_X'})
    Mplt.write(r'./Mapplet.xml')


    MapMapplet = Mapping(name='m_MapMapplet', component_list=[Mplt, Mplt1])
    MapMapplet.write(r'./MapMapplet.xml')