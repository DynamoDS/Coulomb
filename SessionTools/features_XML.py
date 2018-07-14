# Feature extractors for XML files ( 0 < Dynamo < 2)

import xml.etree.ElementTree as ET

def getVersion(b64decodedData):
    et = ET.fromstring(b64decodedData)
    version = et.attrib["Version"]
    return version

def usesListAtLevel(data):
    usesList = data.find('useLevels="True"') > -1
    return usesList

