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
# import storage_utils

MAX_MEM = 3 * 1000 * 1000 * 1000

SESSIONS_BUCKET = "dynamo_instrumentation_sessions"

def session_name_to_sorted_session_name(session_name):
    session_id_split = session_name.split('.gz')[0]
    sorted_session_name = "{}.sorted.gz".format(session_id_split)
    return sorted_session_name

def get_blob_names_to_process(folder_id_str = None):
    if folder_id_str is None:
        folder_id = random.randint(0, 16*16*16)
        folder_id_str = ("%x" % folder_id).zfill(3)

    print ("Selected folder: {}".format(folder_id_str))
    blob_to_date_map = {}

    DATA_FILES_PREFIX = "DynamoData"
    bucket = storage_client.get_bucket(SESSIONS_BUCKET)
    blobs = bucket.list_blobs(prefix=folder_id_str, delimiter=None)
    for blob in blobs:
        if len(blob_to_date_map.keys()) % 1000 == 0:
            log("Blobs: {}".format(len(blob_to_date_map.keys())))
        blob_name = blob.name
        blob_udpated = blob.updated
        blob_to_date_map[blob_name] = blob_udpated
    
    unsorted_blob_names = set()
    for blob_name in blob_to_date_map.keys():
        if not blob_name.endswith('.sorted.gz'):
            unsorted_blob_names.add(blob_name)

    blobs_requiring_sorting = set()
    for unsorted_blob_name in unsorted_blob_names:
        sorted_session_name = session_name_to_sorted_session_name(unsorted_blob_name)

        sorted_session_exists = sorted_session_name in blob_to_date_map.keys()

        if not sorted_session_exists:
            # print ("No sorted session: {}".format(unsorted_blob_name))
            blobs_requiring_sorting.add(unsorted_blob_name)
            continue

        sessions_date = blob_to_date_map[unsorted_blob_name]
        sorted_sessions_date = blob_to_date_map[sorted_session_name]
        requires_update = sessions_date > sorted_sessions_date
        if requires_update:
            blobs_requiring_sorting.add(unsorted_blob_name)
        # print ("Session Date: {}, Sorted Session Date: {}, Requires Update: {}".format(sessions_date, sorted_sessions_date, requires_update))
    
    return list(blobs_requiring_sorting)


def sort_blob(blob_name, sorted_blob_name, temp_path):
    log("Sorting: {} => {}".format(blob_name, sorted_blob_name))

    blob_session_name = blob_name.split('/')[-1]
    blob_session_name_sorted = sorted_blob_name.split('/')[-1]

    blob_path_to_proc = os.path.join(temp_path, blob_session_name)
    out_path = os.path.join(temp_path, blob_session_name_sorted)
    
    log ("Downloading {} => {}".format(blob_name, blob_path_to_proc))
    download_blob(SESSIONS_BUCKET, blob_name, blob_path_to_proc)

    f = gzip.open(blob_path_to_proc)
    data_set = set()
    data = []
    byte_counter = 0
    skip_file = False

    for ln in f:
        data_set.add(ln)
        byte_counter += sys.getsizeof(ln)

        if byte_counter > MAX_MEM:
            skip_file = True
            log ("Skipped large file: " + path)
            log ("Sorted: " + str(i) + ", skipped: " + str(skipped))
            break

    if skip_file:
        os.remove(blob_path_to_proc)
        return False

    for ln in data_set:
        data.append(json.loads(ln))

    data.sort(key=lambda x: int(x["MicroTime"]))
    sortedF = gzip.open(out_path, 'w')
    for d in data:
        sortedF.write((json.dumps(d) + "\n").encode('utf-8'))

    sortedF.flush()
    sortedF.close()
    log("Sorted: {} => {}".format(blob_session_name, blob_session_name_sorted))
    upload_blob(SESSIONS_BUCKET, out_path, sorted_blob_name)
    
    log("About to remove: {}".format(blob_path_to_proc))
    os.remove(blob_path_to_proc)
    
    log("About to remove: {}".format(out_path))
    os.remove(out_path)

    return True

def process_blob_names(blob_names_to_process):
    log ("Blobs to process: {}".format(len(blob_names_to_process)))
    for blob_name in blob_names_to_process:
        sorted_blob_name = session_name_to_sorted_session_name(blob_name)
        result = sort_blob(blob_name, sorted_blob_name, DATA_FILES_TEMP_PATH)

        if not result:
            print ("WARNING: failed to process: {}".format(blob_name))


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print ("Usage: temp_path [linear]")
        print ("Sort and debupe sessions")
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
