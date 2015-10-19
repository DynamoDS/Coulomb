# This tool takes the raw usage data and exports counts of the search queries
# and the cases where the user has added a node to the canvas 

import gzip
import json
import base64 
import sys
import traceback
import time

from os import listdir
from os.path import isfile, join

if len(sys.argv) != 3:
	print "Usage: python search_actions_extract.py path_to_data results_path"
	print "Export the search and accept actions in the logs"
	exit(1)

VERBOSE = False
path = sys.argv[1]
out_path = sys.argv[2]

tagSet = set()
results = []
linesCount = 0
searchCount = 0
err = 0;

print time.strftime("%Y-%m-%d %H:%M:%S"), "LinesCount", "SearchesCount", "Errors Count"

files = [ f for f in listdir(path) if isfile(join(path,f)) ]
for filePath in files:
	f = gzip.open (join(path,filePath));
	for ln in f:
		linesCount += 1

		if linesCount % 10000 == 0:
			print time.strftime("%Y-%m-%d %H:%M:%S"), linesCount, searchCount,err

		try:
			if not ln.startswith("{"):
				continue
			data = json.loads(ln)
			tag = data["Tag"]

			if tag != "Search" and tag != "Search-NodeAdded":
				continue

			searchCount += 1
			result = {}
			result["Session"] = data["SessionID"]
			result["MicroType"] = data["MicroTime"]
			result["Query"] = base64.b64decode(data["Data"])

			if tag == "Search":
				result["Action"] = "SEARCH"

			if tag == "Search-NodeAdded":
				result["Action"] = "ACCEPT"

			if VERBOSE:
				print (result)
				print (result["Session"] + ", " + str(data["MicroTime"]).zfill(10) + ", " + result["Action"] + ", " + result["Query"])

			results.append(result)

		except:
			print filePath
			print "FAILED LINE: "+ ln
			print traceback.format_exc()
			err += 1

print time.strftime("%Y-%m-%d %H:%M:%S"), "Writing results"
out_file = open(out_path, "w")
out_file.write(json.dumps(results))
out_file.close()
print time.strftime("%Y-%m-%d %H:%M:%S"), "Done"
