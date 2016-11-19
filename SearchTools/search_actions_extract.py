# This tool takes the raw usage data and exports counts of the search queries
# and the cases where the user has added a node to the canvas 


import gzip
import json
import base64 
import sys			# Library of system calls
import traceback
import time
import os
from os.path import isfile, join

# Check that the script has been given the right argumets

if len(sys.argv) != 3:
	print "Usage: python search_actions_extract.py path_to_data results_path"
	print "Export the search and accept actions in the logs"
	exit(1)

# Load the arguments into local variables
VERBOSE = True
path = sys.argv[1]			# First command line argument (input path)
out_path = sys.argv[2]		# Second command line argument (results path)

# Setup the tracking data structures

results = []		# Holds the results
linesCount = 0		# Number of lines processed
searchCount = 0		# Number of search messages processed
err = 0;			# Error count

# Print the header row
print time.strftime("%Y-%m-%d %H:%M:%S"), "LinesCount", "SearchesCount", "Errors Count"


# Recursively list the files in sub folders
files = [os.path.join(dp, f) for dp, dn, fn in os.walk(path) for f in fn]
for filePath in files:

	# If the file isn't a sorted file, skip it
	if not filePath.endswith('sorted'):
		continue

	# Open the file, decompressing it as we go
	f = gzip.open (filePath) 

	# Walk over every line in the file
	for ln in f:
		linesCount += 1 # Count them

		# If we've seen 10,000 lines emit a progress indicator message
		if linesCount % 10000 == 0: 
			print time.strftime("%Y-%m-%d %H:%M:%S"), linesCount, searchCount,err

		try:
			if not ln.startswith("{"):
				continue 					# It wasn't a valid data line, maybe a header or an error
			data = json.loads(ln)			# The data lines are JSON packed, so load them into a map

			# At this point `data` contains a map of all the data fields in the message

			tag = data["Tag"]				# Extract the tag

			if tag != "Search" and tag != "Search-NodeAdded": # If it isn't a search message, skip
				continue

			searchCount += 1		
			result = {}						# Assemble an empty result structure

			# Copy over the relevant data
			result["Session"] = data["SessionID"]				# Populate the sessions
			result["MicroTime"] = data["MicroTime"]				# Add the timing
			result["Query"] = base64.b64decode(data["Data"])	# The thing that is being searched for

			# Now manually compute a data item called 'Action', what the user was doing
			if tag == "Search":
				result["Action"] = "SEARCH"

			if tag == "Search-NodeAdded":
				result["Action"] = "ACCEPT"

			# If the Verbose setting flat is set, print the results as we go
			if VERBOSE:
				print (result["Session"] + ", " + str(result["MicroTime"]).zfill(10) + ", " + result["Action"] + ", " + result["Query"])

			# Add this result to the results list
			results.append(result)

		except:
			# If there is a problem, print what went wrong
			print filePath
			print "FAILED LINE: "+ ln
			print traceback.format_exc()
			err += 1

# Output the results into the output file
print time.strftime("%Y-%m-%d %H:%M:%S"), "Writing results"
out_file = open(out_path, "w")
out_file.write(json.dumps(results))
out_file.close()
print time.strftime("%Y-%m-%d %H:%M:%S"), "Done"
