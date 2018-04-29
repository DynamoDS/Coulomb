# This tool takes the raw usage data and lists the available tags

import gzip
import json
import base64
import sys
import traceback
import time

from os import listdir
from os.path import isfile, join

VERBOSE = True

def log(s):
	if VERBOSE:
		print time.strftime("%Y-%m-%d %H:%M:%S"), s

if len(sys.argv) != 2:
	print "Usage: python list_tags.py path_to_data"
	print "Print the tags used in the dataset"
	exit(1)

path = sys.argv[1]

tagSet = set()
linesCount = 0
dataLinesCount = 0
err = 0;

log("Start")

files = [ f for f in listdir(path) if isfile(join(path,f)) ]
for filePath in files:
	f = gzip.open (join(path,filePath));
	for ln in f:
		linesCount += 1

		if linesCount % 10000 == 0:
			log (str(linesCount) + "\t" + str(dataLinesCount) + "\t" + str(err))
		try:
			if not ln.startswith("{"):
				continue
			dataLinesCount += 1
			data = json.loads(ln)
			tag = data["Tag"]

			# Workspace data is post-fixed with the GUID of the workspace
			if tag.startswith("Workspace-"):
				tag = "Workspace"

			# Unseen data
			if tag not in tagSet:
				log ("New tag:\t" + tag)
				tagSet.add(tag)

		except:
			err += 1

log("Printing results")
print tagSet
log("Done")
