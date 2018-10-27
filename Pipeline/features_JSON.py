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
    return False                                        # TODO

def hasLongestLacing(data):
    return False                                        # TODO

def hasDisabledLacing(data):
    return data.find('"Replication": "Disabled"') > -1  # TO CONFIRM

def hasCrossProductLacing(data):
    return False                                        # TODO

def hasPinned(data):
    return False                                        # TODO

def hasFrozen(data):
    return False                                        # TODO
