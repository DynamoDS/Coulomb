while true; do
		mkdir -p ~/working_location
		mkdir -p ~/logs

        now="$(date +'%Y_%m_%d__%H_%M_%S')"
        python3 sessions_to_sorted_deduped_sessions.py ~/working_location linear &> ~/logs/sessions_to_sorted_deduped_sessions-$now.log
        gzip ~/logs/sessions_to_sorted_deduped_sessions-$now.log
       	gsutil mv  ~/logs/sessions_to_sorted_deduped_sessions-$now.log.gz gs://dynamo_instrumentation_logs/sessions_to_sorted_deduped_sessions
done
