# Feature extractors for XML files ( 0 < Dynamo < 2)

import xml.etree.ElementTree as xmlElementTree

def getVersion(b64decodedData):
    et = xmlElementTree.fromstring(b64decodedData)
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

def hasAutoLacing(data):
    return False

def hasFirstLacing(data):
    return False

def hasPinned(data):
    return data.find('isPinned="true"') > -1

def hasFrozen(data):
    return data.find('IsFrozen="true"') > -1  # sic IsFrozen

def hasCodeBlockNode(data):
    workspaceElement = xmlElementTree.fromstring(data)
    for element in workspaceElement.find('Elements'):
        if (element.tag == 'Dynamo.Graph.Nodes.CodeBlockNodeModel'):
            return True
    return False

def hasPythonFunction(data):
    workspaceElement = xmlElementTree.fromstring(data)
    for element in workspaceElement.find('Elements'):
        if (element.tag == 'PythonNodeModels.PythonNode'):
            return True
    return False

def hasCustomFunction(data):
    workspaceElement = xmlElementTree.fromstring(data)
    for element in workspaceElement.find('Elements'):
        if (element.tag == 'Dynamo.Graph.Nodes.CustomNodes.Function'):
            return True
    return False

def computeNodeUsageMap(data):
    nodeUsageMap = {}
    workspaceElement = xmlElementTree.fromstring(data)
    for element in workspaceElement.find('Elements'):
        if (element.tag == 'Dynamo.Graph.Nodes.ZeroTouch.DSFunction'):
            lib_name = element.attrib['assembly'].split('\\')[-1]
            best_name = lib_name + ":" + element.attrib['function']
            nodeUsageMap[best_name] = True
        elif (element.tag == 'Dynamo.Graph.Nodes.ZeroTouch.DSVarArgFunction'):
            lib_name = element.attrib['assembly'].split('\\')[-1]
            best_name = lib_name + ":" + element.attrib['function']
            nodeUsageMap[best_name] = True
        elif (element.tag == 'Dynamo.Graph.Nodes.CustomNodes.Function'):
            custom_node_best_name = element.attrib['nickname'] + " (" + element.find('ID').attrib["value"] + ")"
            nodeUsageMap["CustomFunction: " + custom_node_best_name] = True
        else:
            nodeUsageMap[element.attrib['type']] = True
    return nodeUsageMap
