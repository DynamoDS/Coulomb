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
    
    
VERSION="StackTraces-2018-08-16"        # This is the name of the feature set, update it with any major changes

# Progress counters
processed = 0
skipped = 0
err_count = 0
i = 0


if len(sys.argv) != 2:
    print ("Usage: python stacktrace_extractor.py PathToSessions")

path = sys.argv[1]
paths = []

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
        stackTraces = []
        tags = set()
        userId = None
        version = None
        sessionStartMicroTime = 0
        sessionEndMicroTime = 0
        sessionDate = ''

        # Helper function to export data so far
        # TODO: De-nest this function
        def writeDataToFile():
            if (len(stackTraces) == 0): # If no stack traces, skip
                if os.path.exists(out_path):
                    os.remove(out_path)
                return

            print (json.dumps(
                {
                    "StackTraces" : stackTraces,
                    "Tags" : list(tags),
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
                stackTraces = []
                tags = set()
                sessionStartMicroTime = int(data["MicroTime"])
                sessionDate = data["DateTime"].split(" ")[0]
            sessionEndMicroTime = int(data["MicroTime"])

            # Keep track of what we've seen in the data file
            tags.add(data["Tag"])
            
            # Data is in base64 to protect against special characters, unpack it
            b64decodedData = base64.b64decode(data["Data"])


            # Split what to do based on what kind of message this is
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
                    continue  # Skip JSON coded files for now
                    # feature_lib = features_JSON

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
