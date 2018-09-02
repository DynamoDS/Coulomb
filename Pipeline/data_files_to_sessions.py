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

storage_client = storage.Client()
DATA_FILES_BUCKET = "dynamo_instrumentation_archive_dra_eu"
COMPLETED_DATA_FILES_BUCKET = "dynamo_instrumentation_archive_processed"
SESSIONS_BUCKET = "dynamo_instrumentation_sessions"

if len(sys.argv) != 3:
    print ("Usage: data_files_to_sessions data_files_temp_path session_files_temp_path")
    print ("Extract session files from the raw data")
    exit(1)

DATA_FILES_TEMP_PATH = sys.argv[1]
SESSIONS_FILES_TEMP_PATH = sys.argv[2]

def log(s):
    print (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + ": " + s)

def get_blob_name_to_process():
    DATA_FILES_PREFIX = "DynamoData"
    bucket = storage_client.get_bucket(DATA_FILES_BUCKET)
    blobs = bucket.list_blobs(prefix=DATA_FILES_PREFIX, delimiter=None)
    for blob in blobs:
        blob_name = blob.name
        log ("get_blob_name_to_process: => {}".format(blob_name))
        return blob_name
        # This is clearly crazy as a way of getting an item out of the
        # psuedo-iterator that the Cloud Client library is returning

def ensure_have_session(sessionID):
    prefix = sessionID[0:3]
    filename = sessionID + ".gz"

    local_session_path = os.path.join(SESSIONS_FILES_TEMP_PATH, filename)

    if os.path.exists(local_session_path):
        return local_session_path
    
    source_blob_name = prefix + "/" + filename

    if storage_client.get_bucket(SESSIONS_BUCKET).blob(source_blob_name).exists():
        download_blob(SESSIONS_BUCKET, source_blob_name, local_session_path)
        return local_session_path
    
    log ("New session: " + sessionID)
    newSessionIDSet.add(sessionID)
    return local_session_path


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    log('download_blob: About to download {}.'.format(source_blob_name))

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    log('download_blob: {} downloaded to {}.'.format(
        source_blob_name,
        destination_file_name))


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    log('upload_blob: About to upload {}.'.format(source_file_name))

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    log('upload_blob: {} uploaded to {}.'.format(
        source_file_name,
        destination_blob_name))

def move_blob(bucket_name, blob_name, new_bucket_name):
    """Moves a blob from one bucket to another with a new name."""
    storage_client = storage.Client()
    source_bucket = storage_client.get_bucket(bucket_name)
    source_blob = source_bucket.blob(blob_name)
    destination_bucket = storage_client.get_bucket(new_bucket_name)

    new_blob = source_bucket.copy_blob(
        source_blob, destination_bucket, blob_name)

    log('Blob {} in bucket {} copied to blob {} in bucket {}.'.format(
        source_blob.name, source_bucket.name, new_blob.name,
        destination_bucket.name))
    
    source_blob.delete()
    log('Blob {} deleted.'.format(source_blob))


blob_name_to_proc = get_blob_name_to_process()
blob_path_to_proc = os.path.join(DATA_FILES_TEMP_PATH, blob_name_to_proc)
download_blob(DATA_FILES_BUCKET, blob_name_to_proc, blob_path_to_proc)


def flush(session_maps):
    lns_count = 0
    for sessions_lst in session_maps.values():
        lns_count += len(sessions_lst)

    log ("Flushing lines/sessions: " + str(lns_count) + " / " + str(len(session_maps.keys())))

    # Verify that the folders exist
    for session_id in sorted(session_maps.keys()):
        log ("Flushing session: " + session_id)
        sessionPath = ensure_have_session(session_id)
        log ("Session path: " + sessionPath)
            
        o = gzip.open(sessionPath, 'ab')
        for ln in session_maps[session_id]:
            assert (json.loads(ln)["SessionID"] == session_id)
            o.write(ln)
        o.flush()
        log ("Flushing complete for: " + session_id)

    log ("Flushing complete. Total sessions:\t" + str(len(sessionIDSet)) + "\tTotal new sessions:\t" + str(len(newSessionIDSet)))


newSessionIDSet = set()
sessionIDSet = set()

linesCount = 0
dataLinesCount = 0
err = 0

log("Start")

sessions_maps = {}
byte_counter = 0

filePath = blob_path_to_proc

f = gzip.open(filePath)
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
    # print (ln)
    try:
        if not ln.startswith(b'{'):
            # print (ln)
            continue

        dataLinesCount += 1
        data = json.loads(ln)
        session = data["SessionID"]
        sessionIDSet.add(session)

        if not session in sessions_maps.keys():
            sessions_maps[session] = []
        
        sessions_maps[session].append(ln)

        if byte_counter > 1024 * 1024 * 1024 * 1:
            flush(sessions_maps)
            sessions_maps.clear()
            byte_counter = 0

    except:
        err += 1
        print (ln)
        exit(1)
# Flush lines
flush(sessions_maps)
sessions_maps.clear()

# Verify the files
log ("Verifying gzip files")
files = [ f for f in sorted(os.listdir(SESSIONS_FILES_TEMP_PATH)) if os.path.isfile(os.path.join(SESSIONS_FILES_TEMP_PATH,f)) ]
for filename in files:
    probable_session = filename.split('.')[0]
    filePath = os.path.join(SESSIONS_FILES_TEMP_PATH,filename)
    if not filePath.endswith(".gz"):
        log ("Unexpected file: " + filePath)

    log ("Verifying: " + filePath)

    f = gzip.open(filePath)
    
    for ln in f: # read through the file to verify it decompresses
        assert(json.loads(ln)["SessionID"] == probable_session)
log ("Verification complete")

# Upload the results files
log ("Uploading sessions")

for filename in files:
    filePath = os.path.join(SESSIONS_FILES_TEMP_PATH,filename)
    prefix = filename[0:3]

    if not filePath.endswith(".gz"):
        print ("Unexpected file: " + filePath)
        exit (1)

    destination_blob_name = prefix + "/" + filename
    log ("Uploading: " + filePath + " => " + destination_blob_name)
    upload_blob(SESSIONS_BUCKET, filePath, destination_blob_name)

    log ("Removing: " + filePath)
    os.remove(filePath)

log ("Upload done")

log ("Moving data blob to processed bucket")
move_blob(DATA_FILES_BUCKET, blob_name_to_proc, COMPLETED_DATA_FILES_BUCKET)

log ("Deleting local copy of data file")
os.remove(blob_path_to_proc)

log("Done")

