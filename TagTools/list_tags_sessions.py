# This tool takes the raw usage data and splits it into session files

import gzip
import json
import base64
import sys
import traceback
import time

import os
import sys

VERBOSE = True

def log(s):
    if VERBOSE:
        print time.strftime("%Y-%m-%d %H:%M:%S"), s

if len(sys.argv) != 2:
    print "Usage: python list_tags_sessions.py path_to_sessions"
    print "Sort sessions"
    exit(1)

path = sys.argv[1]

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
            if linesCount % 1000 == 0:
                log(linesCount)

            data = json.loads(ln)
            tag = data["Tag"]

            # Workspace data is post-fixed with the GUID of the workspace
            if tag.startswith("Workspace-"):
                tag = "Workspace"

            if tag not in tags:
                tags.add(tag)
                print tags

print tags