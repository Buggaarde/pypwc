import xml.etree.ElementTree as ET
from Transformations import Expression
from Canvas import Composite, Mapping, Mapplet
    

            # <TRANSFORMFIELD DATATYPE ="bigint" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="in_LINE_NR" PICTURETEXT ="" PORTTYPE ="OUTPUT" PRECISION ="19" SCALE ="0"/>

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

    # Map = Mapping(name='m_Map', component_list=component_list)
    # Map.connect(Exp, Exp1, {'ANDEL_AF_LAAN_X': 'LINE_NR'})
    # Map.write(r'./Map.xml')

    Mapplet = Mapplet(name='mplt_MAPPLET', component_list=component_list)
    Mapplet.connect(Exp, Exp1, {'ANDEL_AF_LAAN_X': 'LINE_NR'})
    Mapplet.write(r'./Mapplet.xml')

    MapMapplet = Mapping(name='m_MapMapplet', component_list=[Mapplet])
    MapMapplet.write(r'./MapMapplet.xml')