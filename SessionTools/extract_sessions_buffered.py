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


def flush(outpath, session_maps):

    lns_count = 0
    for sessions_lst in session_maps.values():
        lns_count += len(sessions_lst)

    log ("Flushing lines/sessions: " + str(lns_count) + " / " + str(len(session_maps.keys())))

    # Verify that the folders exist
    for session in session_maps.keys():
        sessions_folder_path = join(outPath, session[0:3])
        if sessions_folder_path not in existing_sessions_path:
            if not os.path.exists(sessions_folder_path):
                os.makedirs(sessions_folder_path)
            existing_sessions_path.add(sessions_folder_path)

        sessionPath = join(sessions_folder_path, session + ".gz")
        if not os.path.exists(sessionPath):
            newSessionIDSet.add(session)
            

        o = gzip.open(sessionPath, 'a')
        # o = open(join(outPath, session + ".json"), 'a')
        for ln in session_maps[session]:
            o.write(ln)
        o.flush()
    log ("Flushing complete. Total sessions:\t" + str(len(sessionIDSet)) + "\tTotal new sessions:\t" + str(len(newSessionIDSet)))


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
existing_sessions_path = set()

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
    sessions_maps = {}

    byte_counter = 0

    for ln in f:
        linesCount += 1

        byte_counter += sys.getsizeof(ln)

        if linesCount % 1000 == 0:
			log (
                filePath + "\t" + \
                str(linesCount) + "\t" + \
                str(dataLinesCount) + "\t" + 
                str(err) + \
                "\tBuffer(MB):\t" + str(int(byte_counter / (1024 * 1024))))
        
        try:
            if not ln.startswith("{"):
                continue
            dataLinesCount += 1
            data = json.loads(ln)
            session = data["SessionID"]
            sessionIDSet.add(session)

            if not sessions_maps.has_key(session):
                sessions_maps[session] = []
            
            sessions_maps[session].append(ln)

            if byte_counter > 1024 * 1024 * 1024 * 2:
                flush(outPath, sessions_maps)
                sessions_maps.clear()
                byte_counter = 0

        except:
            err += 1
    
    # Flush lines
    flush(outPath, sessions_maps)
    sessions_maps.clear()

    completedInputFiles.add(filePath)
    f = open(completedInputListPath, 'a')
    f.write(filePath + "\n")
    f.flush()

log("Done")

