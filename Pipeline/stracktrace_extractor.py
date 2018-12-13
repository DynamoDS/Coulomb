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
    
VERSION="2018-12-13-Stacktraces"

def extract(path, out_path):
    try:
        f = gzip.open (path)
        fo = open(out_path , 'w')
        stacktraces = []
        sessionStartMicroTime = 0

        # Helper function to export data so far
        # TODO: De-nest this function
        def writeDataToFile():
            print (json.dumps(
                {
                    "StackTraces" : searchMap,
                    "UserID": userId,
                    "WorkspaceVersion": version,
                    "Date": sessionDate,
                }), file=fo)

        # Process each line of the session file
        for bytes_ln in f:
            ln = bytes_ln.decode("utf-8") 
            # ln = str(ln)
            # print (ln)
            # print (type(ln))
            if ln.startswith("Downloading phase"): # Marker from the download script, ignore
                continue
            data = json.loads(ln)

            # Compute the first day
            if sessionStartMicroTime == 0:
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]

            # Data is in base64 to protect against special characters, unpack it
            b64decodedData = base64.b64decode(data["Data"]).decode("utf-8") 

            # Text entered into the search box
            if data["Tag"] == "StackTrace":
                stackTraces.append(b64decodedData)

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
                    feature_lib = features_JSON

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
    # Flush any further data to the file
    writeDataToFile()
