from __future__ import print_function

import json
import xml.etree.ElementTree as xmlElementTree
import base64 
import os
import sys
from os.path import isfile, join
import gzip
import datetime
import random
import traceback
import sys

import features_JSON
import features_XML
    
VERSION="2018-07-15"
processed = 0
skipped = 0
err_count = 0

if len(sys.argv) != 2:
    print ("Usage: python feature_usage_extractor.py PathToSessions")

path = sys.argv[1]

paths = []

def emptyFeatureUsageMap():
    return {
        "ListAtLevel": False,
        "HiddenNodes": False,
        "UpstreamHiddenNodes": False,
        "ShortestLacing": False,
        "LongestLacing": False,
        "Pinned": False,
        "Frozen": False
    }


i = 0

print ('Enumerating files')
for root, subdirs, files in os.walk(path):
    for ff in files:
        i = i + 1
        if i % 1000 == 0:
            print (i)
        path = join(root,ff)
        if (not path.endswith('sorted.gz')):
            continue
        paths.append(path)

random.shuffle(paths)
print ('Paths to process: ' + str(len(paths)))

for path in paths:            
    print (str(datetime.datetime.now()) + ": " + path + ": processed: " + str(processed) + ", errs: " + str(err_count) + ", results_exist: " + str(skipped) + ", total: " + str(processed + skipped) )

    out_path = path + ".features" + "." + VERSION
    # skip files that have been processed already
    if os.path.exists(out_path) and os.path.getmtime(out_path) > os.path.getmtime(path):
        skipped = skipped + 1
        continue

    try:
        f = gzip.open (path)
        fo = open(out_path , 'w')
        processed = processed + 1
        isJSON = False
        searchMap = {}
        searchNodeAdded = {}
        tags = set()
        featureUsageMap = emptyFeatureUsageMap()
        nodeUsageMap = {}
        userId = None
        version = None
        sessionStartMicroTime = 0
        sessionEndMicroTime = 0
        sessionDate = ''

        def writeDataToFile():
            if isJSON: # Don't write results for JSON files for now
                return 

            print (json.dumps(
                {
                    "Searches" : searchMap,
                    "SearchesNodeAdded" : searchNodeAdded,
                    "Tags" : list(tags),
                    "FeatureUsageMap" : featureUsageMap,
                    "NodeUsageMap" : nodeUsageMap,
                    "UserID": userId,
                    "WorkspaceVersion": version,
                    "SessionDuration": sessionEndMicroTime - sessionStartMicroTime,
                    "Date": sessionDate
                }), file=fo)

        for ln in f:
            if ln.startswith("Downloading phase"):
                continue
            data = json.loads(ln)

            if sessionStartMicroTime == 0:
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]
            if sessionDate != data["DateTime"].split(" ")[0]:
                print (path + " has session over multiple days")
                # Split the session: write session so far to file, then reset data collection.
                writeDataToFile()
                searchMap = {}
                searchNodeAdded = {}
                tags = set()
                featureUsageMap = emptyFeatureUsageMap()
                nodeUsageMap = {}
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]
            sessionEndMicroTime = int(data["MicroTime"])

            tags.add(data["Tag"])
            b64decodedData = base64.b64decode(data["Data"])


            if data["Tag"] == "Search":
                searchMap[data["MicroTime"]] = b64decodedData

            if data["Tag"] == "Search-NodeAdded":
                searchNodeAdded[data["MicroTime"]] = b64decodedData

            if data["Tag"] == "Workspace":
                if b64decodedData == '':
                    continue

                # Select which feature extraction library to use depending on what version on the file format 
                feature_lib = None
                if b64decodedData.startswith("<"):
                    feature_lib = features_XML
                else:
                    isJSON = True
                    print ("Skipping JSON based file: " + path)
                    if os.path.exists(out_path):
                        os.remove(out_path)

                    continue  # Skip JSON coded files for now
                    # feature_lib = features_JSON

                featureUsageMap["ListAtLevel"] = featureUsageMap["ListAtLevel"] or feature_lib.usesListAtLevel(b64decodedData)
                featureUsageMap["HiddenNodes"] = featureUsageMap["HiddenNodes"] or feature_lib.hasHiddenNodes(b64decodedData)
                featureUsageMap["UpstreamHiddenNodes"] = featureUsageMap["UpstreamHiddenNodes"] or feature_lib.hasUpstreamHiddenNodes(b64decodedData)
                featureUsageMap["ShortestLacing"] = featureUsageMap["ShortestLacing"] or feature_lib.hasShortestLacing(b64decodedData)
                featureUsageMap["LongestLacing"] = featureUsageMap["LongestLacing"] or feature_lib.hasLongestLacing(b64decodedData)
                featureUsageMap["Pinned"] = featureUsageMap["Pinned"] or feature_lib.hasPinned(b64decodedData)
                featureUsageMap["Frozen"] = featureUsageMap["Frozen"] or feature_lib.hasFrozen(b64decodedData)


                # TOOD: Build the equiavalent to this for JSON
                workspaceElement = xmlElementTree.fromstring(b64decodedData)
                for element in workspaceElement.find('Elements'):
                    if (element.tag == 'Dynamo.Graph.Nodes.ZeroTouch.DSFunction'):
                        nodeUsageMap[element.attrib['function']] = True
                    elif (element.tag == 'Dynamo.Graph.Nodes.ZeroTouch.DSVarArgFunction'):
                        nodeUsageMap[element.attrib['function']] = True
                    else:
                        nodeUsageMap[element.attrib['type']] = True

                if (version == None):
                    version = feature_lib.getVersion(b64decodedData)

            if userId == None:
                userId = data["UserID"]
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print (e)
        print (path)

        traceback.print_tb(exc_traceback, file=sys.stdout)
        fo.flush()
        os.remove(out_path)
        err_count = err_count + 1
        continue

    writeDataToFile()
