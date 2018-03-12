from __future__ import print_function

import json
import base64 
import os
import sys
from os.path import isfile, join
import gzip


def usesListAtLevel(data):
    usesList = data.find('useLevels="True"') > -1
    return usesList
    


if len(sys.argv) != 2:
    print ("Usage: python feature_extractor.py PathToSessions")

path = sys.argv[1]

for root, subdirs, files in os.walk(path):
    for ff in files:
        path = join(root,ff)
        if (not path.endswith('sorted.gz')):
            # print ("SKIPPED: " + path)
            continue
        # print (path)
        f = gzip.open (path)
        fo = open (path + ".features" , 'w')

        searchMap = {}
        searchNodeAdded = {}
        tags = set()

        usageMap = {
            "ListAtLevel": False
        }

        



        for ln in f:
            if ln.startswith("Downloading phase"):
                continue
            try:
                data = json.loads(ln)

                tags.add(data["Tag"])

                if data["Tag"] == "Search":
                    searchMap[data["MicroTime"]] = base64.b64decode(data["Data"])

                if data["Tag"] == "Search-NodeAdded":
                    searchNodeAdded[data["MicroTime"]] = base64.b64decode(data["Data"])

                if data["Tag"] == "Workspace":
                    usageMap["ListAtLevel"] = usageMap["ListAtLevel"] or usesListAtLevel(base64.b64decode(data["Data"]))

                # print (str(data["Tag"]))
				# if data["Tag"] == "Workspace":
					# print (data["SessionID"] + ", " + str(data["MicroTime"]).zfill(10) + ", " + 
						# base64.b64decode(data["Data"]), file=fo)
            except Exception as e:
                print (e)
                # print (ln)

        print (json.dumps(
            {
                "Searches" : searchMap,
                "SearchesNodeAdded" : searchNodeAdded,
                "Tags" : list(tags),
                "UsageMap" : usageMap
            }), file=fo);

