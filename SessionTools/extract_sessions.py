# This tool takes the raw usage data and splits it into session files

import gzip
import json
import base64
import sys
import traceback
import time

from os import listdir
from os.path import isfile, join

import os

VERBOSE = True

def log(s):
    if VERBOSE:
        print time.strftime("%Y-%m-%d %H:%M:%S"), s

if len(sys.argv) != 3:
    print "Usage: python extract_sessions.py path_to_data output_path"
    print "Extract session files from the raw data"
    exit(1)

path = sys.argv[1]
outPath = sys.argv[2]

completedInputListPath = join(outPath, '_completedInputFiles.lst')
completedInputFiles = set()
if os.path.exists(completedInputListPath):
    for ln in open(completedInputListPath, 'r'):
        completedInputFiles.add(ln.strip())


# existingOutFiles = [ f for f in listdir(outPath) if isfile(join(outPath,f)) ]

# if len(existingOutFiles) > 1:
#     print "Out directory not empty"
#     exit(1)


newSessionIDSet = set()
sessionIDSet = set()

linesCount = 0
dataLinesCount = 0
err = 0;

log("Start")

files = [ f for f in listdir(path) if isfile(join(path,f)) ]
for filePath in files:
    if filePath in completedInputFiles:
        log ("Already processed: " + filePath)
        completedInputFiles.add(filePath)
        continue
    f = gzip.open (join(path,filePath));
    for ln in f:
        linesCount += 1

        if linesCount % 1000 == 0:
			log (str(linesCount) + "\t" + str(dataLinesCount) + "\t" + str(err) + "\tNew sessions:\t" + str(len(newSessionIDSet)) + "\tUpdated sessions:\t" + str(len(sessionIDSet)))
        try:
            if not ln.startswith("{"):
                continue
            dataLinesCount += 1
            data = json.loads(ln)
            session = data["SessionID"]
            sessionIDSet.add(session)
            if not os.path.exists(join(outPath, session[0:3])):
                os.makedirs(join(outPath, session[0:3]))

            sessionPath = join(outPath, session[0:3], session + ".gz")
            if not os.path.exists(sessionPath):
                newSessionIDSet.add(session)

            o = gzip.open(sessionPath, 'a')
            # o = open(join(outPath, session + ".json"), 'a')
            o.write(ln)
            o.flush()
        except:
            err += 1
    completedInputFiles.add(filePath)
    f = open(completedInputListPath, 'a')
    f.write(filePath + "\n")
    f.flush()

log("Printing results")
print tagSet
log("Done")
