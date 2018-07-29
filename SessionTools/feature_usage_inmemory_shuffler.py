# Condenses all the feature files into a single location,
# Split by the names of the features


import sys
from os.path import isfile
import os
import json

path = sys.argv[1]
out_path = sys.argv[2]
paths = []

i = 0
skipped = 0

pretty_print_json_output = True

feature_versions_map = {}

def flush():
    # Create one file per feature version
    for k in feature_versions_map.keys():
        out_full_path = out_path + "." + k + '.json'
        data_to_dump = {
            "feature_version" : k,
            "sessions" : feature_versions_map[k]
        }

        with open(out_full_path, 'w') as f:
            if pretty_print_json_output:
                f.write(json.dumps(data_to_dump, sort_keys=True, indent=2))
            else:
                f.write(json.dumps(data_to_dump))


# Main function

print ('Enumerating feature files')

for root, subdirs, files in os.walk(path):
    for ff in files:
        i = i + 1
        if i % 1000 == 0:
            print (i, skipped)
            flush()

        path = os.path.join(root,ff)
        if (path.find('.sorted.gz.features.') == -1 ):
            continue
        path_split = path.split ('.sorted.gz.features.')

        feature_version = path_split[-1]
        if not feature_versions_map.has_key(feature_version):
            feature_versions_map[feature_version] = {}

        session_id = path_split[0].split('/')[-1]


        
        if feature_versions_map[feature_version].has_key(session_id):
            # We've already added this session
            # This can be used in a version that loads a partially complete file
            print ("Session: ") + session_id + " skipped, features already added for: " + feature_version
            skipped += 1
            continue
        feature_versions_map[feature_version][session_id] = []

        paths.append(path)
        print (feature_version, session_id, path)

        with open(path, 'r') as f:
            lines = f.readlines()
            for ln in lines:
                feature_versions_map[feature_version][session_id].append(json.loads(ln))

flush()
    
                