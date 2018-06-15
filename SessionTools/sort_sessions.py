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

def compute_derived_path(s):
    return s[:-3] + ".sorted.gz"

if len(sys.argv) != 2:
    print "Usage: python sort_sessions.py path_to_sessions"
    print "Sort sessions"
    exit(1)

path = sys.argv[1]



paths_to_test = set()
sorted_paths = set()

linesCount = 0
paths_count = 0
for root, subdirs, files in os.walk(path):
    for ff in files:
        paths_count += 1
        if paths_count % 1000 == 0:
            log ("Enumerating paths: " + str(paths_count))
        path = os.path.join(root, ff)
        if path.endswith('.sorted.gz'):
            sorted_paths.add(path)
            continue
        if not path.endswith('.gz'):
            continue
        paths_to_test.add(path)

log ("All paths: " + str(len(paths_to_test)))
already_sorted = 0
paths_to_sort = set()
for test_path in paths_to_test:
    if compute_derived_path(test_path) in sorted_paths:
        already_sorted += 1
        continue
    paths_to_sort.add(test_path)

log ("Sorting: " + str(len(paths_to_sort)) + ", already sorted: " + str(already_sorted))

i = 0
skipped = 0
for path in paths_to_sort:
    i += 1
    if i % 1000 == 0:
        log ("Sorted: " + str(i) + ", " + str((100*i) / len(paths_to_sort)) + ", skipped: " + str(skipped))
    out_path = compute_derived_path(path)
    # skip files that have been processed already between start of the script and now
    if os.path.exists(out_path):
        skipped += 1
        continue
    try:
        log(path)
        f = gzip.open(path)
        data_set = set()
        data = []
        for ln in f:
            data_set.add(ln)

        for ln in data_set:
            data.append(json.loads(ln))

        data.sort(key=lambda x: int(x["MicroTime"]))

        sortedF = gzip.open(out_path, 'w')

        for d in data:
            sortedF.write(json.dumps(d) + "\n")

        sortedF.flush()
        sortedF.close()
    except:
        err += 1
        log ("Failed: " + str(err))
