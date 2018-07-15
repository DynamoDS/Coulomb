# Tool to expand a sorted session for manual inspection

import json
import xml.etree.ElementTree as xmlElementTree
import xml.dom.minidom
import base64 
import os
import sys
from os.path import isfile, join
import gzip
import datetime

import features_JSON
import features_XML

if len(sys.argv) != 2:
    print ("Usage: python diagnostics_expand_session_file.py sorted_session_file_to_expand")

path = sys.argv[1]

# Export the workspaces found to the current working directory?
EXPORT_WORKSPACES = True

f = gzip.open (path)
for ln in f:
    if ln.startswith("Downloading phase"):
        continue
    data = json.loads(ln)
    
    print("")
    print("")
    print("")
    print ("Raw line with data limited to 80 chars")
    print ("~~~~~~~~~~~~~~~~~~~~~~~~")

    data_to_print = data.copy()
    if len(data_to_print["Data"]) > 80:
        data_to_print["Data"] = data["Data"][:77] + "..."
    
    print (data_to_print)
    print ("~~~~~~~~~~~~~~~~~~~~~~~~")

    microtime = data["MicroTime"]

    print "Time:\t\t\t" + str(microtime)

    print "Tag:\t\t\t" + data["Tag"]
    b64decodedData = base64.b64decode(data["Data"])
    
    if data["Tag"] == "Search":
        print ("Search:\t\t\t" + b64decodedData)


    if data["Tag"] == "Search-NodeAdded":
        print ("Search node added:\t" + b64decodedData)

    if data["Tag"] == "Workspace":
        if EXPORT_WORKSPACES:
            if (b64decodedData.startswith("<")):   # XML based
                f_name = microtime + ".xml"
                with open(f_name, 'w') as f_dump:
                    xml_dump = xml.dom.minidom.parseString(b64decodedData) 
                    pretty_xml_as_string = xml_dump.toprettyxml()
                    f_dump.write(pretty_xml_as_string.encode('utf-8'))
                    print ("Workspace exported:\t" + f_name)
            elif (b64decodedData.startswith("{")): # JSON based
                f_name = microtime + ".json"
                with open(f_name, 'w') as f_dump:
                    json_dump = json.dumps(json.loads(b64decodedData), sort_keys=True, indent=2)
                    f_dump.write(json_dump.encode('utf-8'))
                    print ("Workspace exported:\t" + f_name)
            else:
                raise "Unknown workspace format"

    print ("~~~~~~~~~~~~~~~~~~~~~~~~")
