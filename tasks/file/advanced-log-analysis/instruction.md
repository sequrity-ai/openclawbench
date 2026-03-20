# Advanced Log Analysis

Parse /workspace/application.log and generate statistics. Create a JSON file named 'log_analysis.json' in /workspace with the following metrics: 1) error_count (number of ERROR entries), 2) warn_count (number of WARN entries), 3) info_count (number of INFO entries), 4) total_entries (total log lines), 5) hourly_distribution (count of entries per hour if you can extract timestamps). Parse the log file line by line and count entries by level.
