
COUNTER=0
while [  $COUNTER -lt 100000 ]; do
 NOW=$(date '+%Y_%m_%d_%H_%M_%S')
 echo $NOW
 dart bin/main.dart ~/Communications/CryptoTokens/dynamoinstr.json download >> ~/USAGE_MOUNT/dynamoinstr/RawExport/DynamoData_$NOW.json
 let COUNTER=COUNTER+1
 gzip ~/USAGE_MOUNT/dynamoinstr/RawExport/DynamoData_$NOW.json
 gsutil -m cp -n ~/USAGE_MOUNT/dynamoinstr/RawExport/DynamoData_$NOW.json.gz gs://dynamo_instrumentation_archive_dra_eu
 sleep 60s

done
