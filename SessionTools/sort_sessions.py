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
err = 0

def log(s):
    if VERBOSE:
        print time.strftime("%Y-%m-%d %H:%M:%S"), s

if len(sys.argv) != 2:
    print "Usage: python sort_sessions.py path_to_sessions"
    print "Sort sessions"
    exit(1)

path = sys.argv[1]

linesCount = 0

for root, subdirs, files in os.walk(path):
    for ff in files:
        try:
            path = os.path.join(root, ff)
            if not path.endswith('.gz'):
                continue
            log(path)
            f = gzip.open(path)
            data = []
            for ln in f:
                data.append(json.loads(ln))

            data.sort(key=lambda x: int(x["MicroTime"]))

            sortedF = gzip.open(os.path.join(root, ff + ".sorted"), 'w')

            for d in data:
                sortedF.write(json.dumps(d) + "\n")

            sortedF.flush()
            sortedF.close()
        except:
            err += 1
            log ("Failed: " + str(err))