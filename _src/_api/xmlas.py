import xml.etree.ElementTree as ET


def load_xml(path):
    tree = ET.parse(path)
    return tree

def save_xml(tree, path):
    with open(path, "wb") as file:
        tree.write(file, encoding='utf-8', xml_declaration=True)
    return 0

def change_txt_nv_key_value(tree, key, value):
    root = tree.getroot()
    for i in root:
        if i[0].text == key:
            i[1].text = value
    return tree

def get_txt_nv_key_value(tree,key):
    root = tree.getroot()
    for i in root:
        if i[0].text == key:
            value = i[1].text
    return value

if __name__ == "__main__":
    pass
