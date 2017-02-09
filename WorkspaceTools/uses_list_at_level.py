# This tool walks over a dataset and reports how many workspaes have at least one use of 
# list at level

import gzip
import json
import base64
import sys
import traceback
import time

from os import listdir
from os.path import isfile, join
from collections import defaultdict

import os



VERBOSE = True

def log(s):
    if VERBOSE:
        print time.strftime("%Y-%m-%d %H:%M:%S"), s

if len(sys.argv) != 3:
    print "Usage: python export_workspaces.py path_to_data out_path"
    print "Walk over sessions files to export whether it uses"
    print "list at level"
    exit(1)

path = sys.argv[1]
outPath = sys.argv[2]

linesCount = 0
dataLinesCount = 0
err = 0;

dtWsCount = {}


def updateResultFile():
    outF = open(outPath, 'w')
    outF.write("Date, No L@L, L@L\n")
    for k in sorted(dtWsCount):
        v = dtWsCount[k]
        outF.write(k + ", " + str(v[False]) + ", " + str(v[True]) + "\n")
        outF.flush()

log("Start")

files = [ f for f in listdir(path) if isfile(join(path,f)) ]
for filePath in files:
    f = gzip.open (join(path,filePath));
    for ln in f:
        linesCount += 1

        if linesCount % 1000 == 0:
            updateResultFile()
            log (str(linesCount))
			# log (str(linesCount) + "\t" + str(dataLinesCount) + "\t" + str(err) + "\tNew sessions:\t" + str(len(newSessionIDSet)) + "\tUpdated sessions:\t" + str(len(sessionIDSet)))
        try:
            if not ln.startswith("{"):
                continue
            dataLinesCount += 1
            data = json.loads(ln)
            session = data["SessionID"]
            serverDate = data["b75e7a7f_ServerDate"]
            tag = data["Tag"]

            if (tag.startswith("Workspace")):
                data = base64.b64decode(data["Data"])
                usesListAtLevel = False
                usesListAtLevel = data.find('useLevels="True"') > -1

                if not dtWsCount.has_key(serverDate):
                    dtWsCount[serverDate] = {}
                    dtWsCount[serverDate][False] = 0
                    dtWsCount[serverDate][True] = 0
                    
                dtWsCount[serverDate][usesListAtLevel] += 1

                # print (dtWsCount)
                # print (session + ",\t" + serverDate + ",\t")

        except err:
            err += 1
            print err

log("Printing results")
