# Tool to export a count of the search terms
# This expects the data in the format that would be exported 
# by search_actions_extract.py

import gzip
import json
import base64 
import sys
import traceback
import time

from collections import Counter

from os import listdir
from os.path import isfile, join

if len(sys.argv) != 2:
	print "Usage: python search_results_proc.py path_search_queries"
	print "Print frequency of search terms"
	exit(1)

path = sys.argv[1]

err = 0;
print time.strftime("%Y-%m-%d %H:%M:%S"), "Starting"

f = open (path)
d = f.read()
results = json.loads(d)

terms = []
for result in results:
	# Ignore the acceptances data
	if result["Action"] != "SEARCH":
		continue

	term = result["Query"]
	terms.append(term)

c = Counter(terms)
for item in c.items():
	print (str(item)).split('(u')[1].split(')')[0]

print time.strftime("%Y-%m-%d %H:%M:%S"), "Done"
