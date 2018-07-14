from __future__ import print_function

import json
import xml.etree.ElementTree as ET
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
        fo = open (out_path , 'w')
        processed = processed + 1
        searchMap = {}
        searchNodeAdded = {}
        tags = set()
        usageMap = { # When adding features here, don't forget to add below as well
            "ListAtLevel": False
        }
        userId = None
        version = None
        sessionStartMicroTime = 0
        sessionEndMicroTime = 0
        sessionDate = ''

        def writeDataToFile():
            print (json.dumps(
                {
                    "Searches" : searchMap,
                    "SearchesNodeAdded" : searchNodeAdded,
                    "Tags" : list(tags),
                    "UsageMap" : usageMap,
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
                usageMap = {
                    "ListAtLevel": False
                }
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
                    feature_lib = features_JSON

                usageMap["ListAtLevel"] = usageMap["ListAtLevel"] or feature_lib.usesListAtLevel(b64decodedData)
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
