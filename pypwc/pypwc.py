import xml.etree.ElementTree as ET
from Transformations import Expression
    

            # <TRANSFORMFIELD DATATYPE ="bigint" DEFAULTVALUE ="" DESCRIPTION ="" NAME ="in_LINE_NR" PICTURETEXT ="" PORTTYPE ="OUTPUT" PRECISION ="19" SCALE ="0"/>

if __name__ == '__main__':
    Exp = Expression()
    Exp.type = 'Aggregator'
    Exp.name = 'Test<>&'
    # print(Exp.name)
    Exp.reusable = 'yes'
    # print(Exp.reusable)
    # print(Exp.attributes)
    # print(Exp.fields)
    # print()
    # ET.dump(Exp.as_xml())
    Exp.write(r'./test.xml')