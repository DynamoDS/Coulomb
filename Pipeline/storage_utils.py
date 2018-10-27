import time
from google.cloud import storage


storage_client = storage.Client()

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

def log(s):
    print (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + ": " + s)
