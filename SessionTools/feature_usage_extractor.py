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
    
VERSION="2018-07-16"        # This is the name of the feature set, update it with any major changes

# Progress counters
processed = 0
skipped = 0
err_count = 0
i = 0


if len(sys.argv) != 2:
    print ("Usage: python feature_usage_extractor.py PathToSessions")

path = sys.argv[1]
paths = []

# A list of all the usages features that are currently extracted
def emptyFeatureUsageMap():
    return {
        "ListAtLevel": False,
        "HiddenNodes": False,
        "UpstreamHiddenNodes": False,
        "ShortestLacing": False,
        "LongestLacing": False,
        "DisabledLacing": False,
        "CrossProductLacing": False,
        "Pinned": False,
        "Frozen": False,
        "CustomFunction": False
    }


# Walk over the dataset computing a list of all the files to process
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

# Randomise them in order to avoid collisions + leapfrogging problems with distributed workers
# If processing locally removing this may slightly improve performance
random.shuffle(paths)

print ('Paths to process: ' + str(len(paths)))
for path in paths:
    
    # Report progress
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

        # Initialise structures for this day
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

        # Helper function to export data so far
        # TODO: De-nest this function
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


        # Process each line of the session file
        for ln in f:
            if ln.startswith("Downloading phase"): # Marker from the download script, ignore
                continue
            data = json.loads(ln)

            # Compute the first day
            if sessionStartMicroTime == 0:
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]

            # If a day has rolled over, export the data
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

            # Keep track of what we've seen in the data file
            tags.add(data["Tag"])
            
            # Data is in base64 to protect against special characters, unpack it
            b64decodedData = base64.b64decode(data["Data"])


            # Split what to do based on what kind of message this is
            # Text entered into the search box
            if data["Tag"] == "Search":
                searchMap[data["MicroTime"]] = b64decodedData

            # A node being added to the canvas from the search UI
            if data["Tag"] == "Search-NodeAdded":
                searchNodeAdded[data["MicroTime"]] = b64decodedData

            # A workspace being reported
            if data["Tag"] == "Workspace":
                if b64decodedData == '':    # An empty workspace, ignore
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

                
                # Extract usage features from the workspace
                featureUsageMap["ListAtLevel"] = featureUsageMap["ListAtLevel"] or feature_lib.usesListAtLevel(b64decodedData)
                featureUsageMap["HiddenNodes"] = featureUsageMap["HiddenNodes"] or feature_lib.hasHiddenNodes(b64decodedData)
                featureUsageMap["UpstreamHiddenNodes"] = featureUsageMap["UpstreamHiddenNodes"] or feature_lib.hasUpstreamHiddenNodes(b64decodedData)
                featureUsageMap["ShortestLacing"] = featureUsageMap["ShortestLacing"] or feature_lib.hasShortestLacing(b64decodedData)
                featureUsageMap["LongestLacing"] = featureUsageMap["LongestLacing"] or feature_lib.hasLongestLacing(b64decodedData)
                featureUsageMap["DisabledLacing"] = featureUsageMap["DisabledLacing"] or feature_lib.hasDisabledLacing(b64decodedData)
                featureUsageMap["CrossProductLacing"] = featureUsageMap["CrossProductLacing"] or feature_lib.hasCrossProductLacing(b64decodedData)
                featureUsageMap["Pinned"] = featureUsageMap["Pinned"] or feature_lib.hasPinned(b64decodedData)
                featureUsageMap["Frozen"] = featureUsageMap["Frozen"] or feature_lib.hasFrozen(b64decodedData)


                # TOOD: Build the equiavalent to this for JSON
                workspaceElement = xmlElementTree.fromstring(b64decodedData)
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
                        featureUsageMap["CustomFunction"] = True
                        custom_node_best_name = element.attrib['nickname'] + " (" + element.find('ID').attrib["value"] + ")"
                        nodeUsageMap["CustomFunction: " + custom_node_best_name] = True
                    else:
                        nodeUsageMap[element.attrib['type']] = True
                
                # Extract version number (first time only)
                if (version == None):
                    version = feature_lib.getVersion(b64decodedData)

            # Extract user ID (first time only)
            if userId == None:
                userId = data["UserID"]
    except Exception as e:
        # If there were a problem, get the stack trace for what happeend
        exc_type, exc_value, exc_traceback = sys.exc_info()

        # Log it
        print (e)
        print (path)
        traceback.print_tb(exc_traceback, file=sys.stdout)
        
        # Remove partial results
        fo.flush()
        os.remove(out_path)
        err_count = err_count + 1
        continue

    # Flush any further data to the file
    writeDataToFile()
