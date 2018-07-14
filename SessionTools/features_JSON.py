import json

def getVersion(b64decodedData):
    json_map = json.loads(b64decodedData)
    if not json_map.has_key("View"):
        return None
    return json.loads(b64decodedData)["View"]["Dynamo"]["Version"]

def usesListAtLevel(data):
    usesList = data.find('"UseLevels": true') > -1
    return usesList