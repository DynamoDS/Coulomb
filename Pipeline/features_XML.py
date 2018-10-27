# Feature extractors for XML files ( 0 < Dynamo < 2)

import xml.etree.ElementTree as ET

def getVersion(b64decodedData):
    et = ET.fromstring(b64decodedData)
    version = et.attrib["Version"]
    return version

def usesListAtLevel(data):
    usesList = data.find('useLevels="True"') > -1
    return usesList

def hasHiddenNodes(data):
    return data.find('isVisible="false"') > -1

def hasUpstreamHiddenNodes(data):
    return data.find('isUpstreamVisible="false"') > -1

def hasShortestLacing(data):
    return data.find('lacing="Shortest"') > -1

def hasLongestLacing(data):
    return data.find('lacing="Longest"') > -1

def hasDisabledLacing(data):
    return data.find('lacing="Disabled"') > -1

def hasCrossProductLacing(data):
    return data.find('lacing="CrossProduct"') > -1

def hasPinned(data):
    return data.find('isPinned="true"') > -1

def hasFrozen(data):
    return data.find('IsFrozen="true"') > -1  # sic IsFrozen
