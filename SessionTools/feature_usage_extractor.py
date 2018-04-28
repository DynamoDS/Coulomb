from __future__ import print_function

import json
import xml.etree.ElementTree as ET
import base64 
import os
import sys
from os.path import isfile, join
import gzip
import datetime


def usesListAtLevel(data):
    usesList = data.find('useLevels="True"') > -1
    return usesList
    
VERSION="2018-04-27"
processed = 0
skipped = 0
err_count = 0


if len(sys.argv) != 2:
    print ("Usage: python feature_usage_extractor.py PathToSessions")

path = sys.argv[1]

for root, subdirs, files in os.walk(path):
    for ff in files:
        path = join(root,ff)
        if (not path.endswith('sorted.gz')):
            continue
            
        print (str(datetime.datetime.now()) + ": processed: " + str(processed) + ", errs: " + str(err_count) + ", results_exist: " + str(skipped) + ", total: " + str(processed + skipped) )

        out_path = path + ".features" + "." + VERSION
        # skip files that have been processed already
        if os.path.exists(out_path) and os.path.getmtime(out_path) > os.path.getmtime(path):
            skipped = skipped + 1
            continue

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
            try:
                data = json.loads(ln)

                if sessionStartMicroTime == 0:
                    sessionStartMicroTime = int(data["MicroTime"])
                    sessionDate = data["DateTime"].split(" ")[0]
                if sessionDate != data["DateTime"].split(" ")[0]:
                    print ("File " + ff + " has session over multiple days")
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

                if data["Tag"] == "Search":
                    searchMap[data["MicroTime"]] = base64.b64decode(data["Data"])

                if data["Tag"] == "Search-NodeAdded":
                    searchNodeAdded[data["MicroTime"]] = base64.b64decode(data["Data"])

                if data["Tag"] == "Workspace":
                    usageMap["ListAtLevel"] = usageMap["ListAtLevel"] or usesListAtLevel(base64.b64decode(data["Data"]))
                    if (version == None):
                        version = ET.fromstring(base64.b64decode(data["Data"])).attrib["Version"]

                if userId == None:
                    userId = data["UserID"]

            except Exception as e:
                print (e)
                print (ff)
                err_count = err_count + 1

        writeDataToFile()
