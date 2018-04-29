# This tool takes the raw usage data and splits it into session files

import gzip
import json
import base64
import sys
import traceback
import time

import os
import sys

VERBOSE = False

def log(s):
    if VERBOSE:
        print time.strftime("%Y-%m-%d %H:%M:%S"), s

def printData(m, decoded):
    print str(m["SessionID"]) + ", " + str(m["MicroTime"]) + ", " + decoded

def barePrintData(m, decoded):
    print decoded

if len(sys.argv) < 3:
    print "Usage: python list_data_by_tag.py path_to_sessions tag [clean]"
    print "List the data for a specific tag sessions"
    exit(1)

path = sys.argv[1]
tagToShow = sys.argv[2]
bare = False

if len(sys.argv) == 4:
    bare = sys.argv[3] == "clean"

linesCount = 0
tags = set()

for root, subdirs, files in os.walk(path):
    for ff in files:
        path = os.path.join(root, ff)
        if not path.endswith(".gz.sorted"):
            continue
        f = gzip.open(path)
        for ln in f:
            linesCount += 1
            if linesCount % 1000 == 0 and not bare:
                log(linesCount)

            data = json.loads(ln)
            tag = data["Tag"]

            # Workspace data is post-fixed with the GUID of the workspace
            if tag.startswith("Workspace-"):
                tag = "Workspace"

            if tag == tagToShow:
                if bare:
                    barePrintData(data, base64.b64decode(data["Data"]))
                else:
                    printData(data, base64.b64decode(data["Data"]))