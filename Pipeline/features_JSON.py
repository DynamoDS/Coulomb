# Feature extractors for JSON files (Dynamo 2+)

import json

def getVersion(b64decodedData):
    json_map = json.loads(b64decodedData)
    if not "View" in json_map.keys():
        return None
    return json_map["View"]["Dynamo"]["Version"]

def usesListAtLevel(data):
    usesList = data.find('"UseLevels": true') > -1
    return usesList

def hasHiddenNodes(data):
    return data.find('"ShowGeometry": false,') > -1     # TO CONFIRM

def hasUpstreamHiddenNodes(data):
    return False                                        # TODO

def hasShortestLacing(data):
    return data.find('"Replication": "Shortest"') > -1

def hasLongestLacing(data):
    return data.find('"Replication": "Longest"') > -1

def hasDisabledLacing(data):
    return data.find('"Replication": "Disabled"') > -1

def hasCrossProductLacing(data):
    return data.find('"Replication": "CrossProduct"') > -1

def hasAutoLacing(data):
    return data.find('"Replication": "Auto"') > -1

def hasFirstLacing(data):
    return data.find('"Replication": "First"') > -1

def hasPinned(data):
    return False                                        # TODO

def hasFrozen(data):
    return False                                        # TODO

def hasCodeBlockNode(data):
    json_map = json.loads(data)
    nodes_list = json_map["Nodes"]
    for node in nodes_list:
        if node["ConcreteType"] == "Dynamo.Graph.Nodes.CodeBlockNodeModel, DynamoCore":
            return True
    return False

def hasPythonFunction(data):
    json_map = json.loads(data)
    nodes_list = json_map["Nodes"]
    for node in nodes_list:
        if node["ConcreteType"] == "PythonNodeModels.PythonNode, PythonNodeModels":
            return True
    return False

def hasCustomFunction(data):
    json_map = json.loads(data)
    nodes_list = json_map["Nodes"]
    for node in nodes_list:
        if node["ConcreteType"] == "Dynamo.Graph.Nodes.CustomNodes.Function, DynamoCore":
            return True
    return False
    

def computeNodeUsageMap(data):
    nodeUsageMap = {}
    json_map = json.loads(data)
    nodes_list = json_map["Nodes"]
    for node in nodes_list:
        concrete_type = node["ConcreteType"]
        node_type = node["NodeType"]
        if node_type == "ExtensionNode":
            best_name = concrete_type.split(',')[0]
            nodeUsageMap[best_name] = True
            continue
        elif node_type == "FunctionNode":
            function_signature = node["FunctionSignature"]
            if concrete_type.startswith("Dynamo.Graph.Nodes.ZeroTouch.DSFunction") or \
                concrete_type.startswith("Dynamo.Graph.Nodes.ZeroTouch.DSVarArgFunction"):
                best_name = function_signature
                nodeUsageMap[best_name] = True
        else:
            nodeUsageMap[node_type] = True
    return nodeUsageMap
