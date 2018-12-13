# This tool takes the raw usage data and splits it into session files

from google.cloud import storage
import os
import time

import gzip
import json
import base64
import sys
import traceback
import time
import random

from storage_utils import download_blob, upload_blob, log, storage_client
from feature_usage_extractor import extract, VERSION
# import storage_utils

MAX_MEM = 1 * 1000 * 1000 * 1000

SESSIONS_BUCKET = "dynamo_instrumentation_sessions"
FEATURES_BUCKET = "dynamo_instrumentation_features"

def sorted_session_name_to_features_name(sorted_session_name):
    features_name = "{}.features.{}".format(sorted_session_name, VERSION)
    return features_name

def get_blob_names_to_process(folder_id_str = None):
    if folder_id_str is None:
        folder_id = random.randint(0, 16*16*16)
        folder_id_str = ("%x" % folder_id).zfill(3)

    print ("Selected folder: {}".format(folder_id_str))
    sessions_blob_to_date_map = {}
    blobs_requiring_extraction = set()

    bucket = storage_client.get_bucket(SESSIONS_BUCKET) 
    sessions_blobs = bucket.list_blobs(prefix=folder_id_str, delimiter=None)
    for sessions_blob in sessions_blobs:
        blob_name = sessions_blob.name
        if not blob_name.endswith('.sorted.gz'):
            continue
        blob_udpated = sessions_blob.updated
        sessions_blob_to_date_map[blob_name] = blob_udpated
    log("Blobs ({}): {}".format(SESSIONS_BUCKET, len(sessions_blob_to_date_map.keys())))
    
    featuress_blob_to_date_map = {}
    bucket = storage_client.get_bucket(FEATURES_BUCKET)
    features_blobs = bucket.list_blobs(prefix=folder_id_str, delimiter=None)
    for feature_blob in features_blobs:
        blob_name = feature_blob.name
        blob_udpated = feature_blob.updated
        featuress_blob_to_date_map[blob_name] = blob_udpated
    log("Blobs ({}): {}".format(FEATURES_BUCKET, len(featuress_blob_to_date_map.keys())))


    missing = 0
    update = 0
    already_done = 0

    for session_blob in sessions_blob_to_date_map.keys():
        features_name = sorted_session_name_to_features_name(session_blob)
        if features_name not in featuress_blob_to_date_map.keys():
            missing += 1
            blobs_requiring_extraction.add(session_blob)
            continue
        
        session_updated = sessions_blob_to_date_map[session_blob]
        features_updated = featuress_blob_to_date_map[features_name]

        if session_updated >= features_updated:
            update += 1
            blobs_requiring_extraction.add(session_blob)
            continue

        already_done += 1
        
    log("Feature extraction needed: {} | {} (missing), {} (update)  | {} (already_done)"
        .format(len(blobs_requiring_extraction), missing, update, already_done))
    return list(blobs_requiring_extraction)


def extract_features(blob_name, features_blob_name, temp_path):
    log("Extract features for ({}): {} => {}".format(VERSION, blob_name, features_blob_name))

    blob_session_name = blob_name.split('/')[-1]
    features_session_name = features_blob_name.split('/')[-1]

    blob_path_to_proc = os.path.join(temp_path, blob_session_name)
    out_path = os.path.join(temp_path, features_session_name)
    
    log ("Downloading {} => {}".format(blob_name, blob_path_to_proc))
    download_blob(SESSIONS_BUCKET, blob_name, blob_path_to_proc)

    extract(blob_path_to_proc, out_path)
    log("Features extracted: {} => {}".format(blob_path_to_proc, out_path))

    if not os.path.exists(out_path):
        return False
        
    upload_blob(FEATURES_BUCKET, out_path, features_blob_name)

    log("About to remove: {}".format(blob_path_to_proc))
    os.remove(blob_path_to_proc)
    
    log("About to remove: {}".format(out_path))
    os.remove(out_path)

    return True

def process_blob_names(blob_names_to_process):
    log ("Blobs to process: {}".format(len(blob_names_to_process)))
    for blob_name in blob_names_to_process:
        features_blob_name = sorted_session_name_to_features_name(blob_name)
        result = extract_features(blob_name, features_blob_name, DATA_FILES_TEMP_PATH)

        if not result:
            print ("WARNING: failed to process: {}".format(blob_name))


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print ("Usage: temp_path [linear]")
        print ("Extract features for sessions")
        print 
        exit(1)

    DATA_FILES_TEMP_PATH = sys.argv[1]
    LINEAR = False
    if len(sys.argv) == 3 and sys.argv[2] == "linear":
        log ("Linear mode")
        LINEAR = True

    if LINEAR:
        for i in range(16*16*16):
            folder_id_str = ("%x" % i).zfill(3)
            blob_names_to_process = get_blob_names_to_process(folder_id_str)
            process_blob_names(blob_names_to_process)
    else:
        blob_names_to_process = get_blob_names_to_process()
        process_blob_names(blob_names_to_process)
