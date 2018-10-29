while true; do
		mkdir -p ~/working_location
		mkdir -p ~/logs

        now="$(date +'%Y_%m_%d__%H_%M_%S')"
        python3 sorted_sessions_to_features.py ~/working_location linear &> ~/logs/feature_extractor-$now.log
        gzip ~/logs/feature_extractor-$now.log
       	gsutil mv  ~/logs/feature_extractor-$now.log.gz gs://dynamo_instrumentation_logs/feature_extractor
done
