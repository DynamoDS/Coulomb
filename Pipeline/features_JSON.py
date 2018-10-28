# Feature extractors for JSON files (Dynamo 2+)

import json

def getVersion(b64decodedData):
    json_map = json.loads(b64decodedData)
    if not json_map.has_key("View"):
        return None
    return json.loads(b64decodedData)["View"]["Dynamo"]["Version"]

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
