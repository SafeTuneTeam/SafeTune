## Target systems
In `Ubuntu 18.04`
```bash
sudo apt install postgresql
sudo apt install cassandra
```

## Workloads used in testing

### PostgreSQL
 - [TPC-C](https://github.com/Percona-Lab/sysbench-tpcc)
 - [TPC-H](https://github.com/electrum/tpch-dbgen)

### Cassandra
 - [NoSQLBench](https://github.com/nosqlbench/nosqlbench)
 - [tlp-stress](https://thelastpickle.com/tlp-stress/)
 - [Cassandra-stress](https://cassandra.apache.org/doc/4.0/cassandra/tools/cassandra_stress.html)

## Testing scripts/commands
We write a testing script for __PostgreSQL__ to run the two benchmarks automatically.
First, `cd scripts/TPC-C` or `cd scripts/TPC-H`, then set the parameter to be tested. In this paper, we tested all parameters that are identified as performance-related by __SafeTune__.
```bash
# Devices you want to run PostgreSQL on. 
# make sure that "/mnt/${DEV}/postgresql-data" exist for DEV in DEVICES.
DEVICES=(sata-s4510)
workload_prefix="change_me" # directory of the workload executable file
conf_name="commit_delay"    # PostgreSQL parameter name
conf_value=(0 100 200 300)  # PostgreSQL parameter values
```
Next, start running just via this simple command:
```bash
bash run-confs.sh > LOG-CONFS-SafeTune.txt
```
You can watch `LOG-CONFS-SafeTune.txt` to see the raw results, or visualize it via this simple command:
```bash
python3 txt2csv.py LOG-CONFS-SafeTune.txt latency
```
You can see the result like this:

For __Cassandra__, we manually test by exhaustively change parameter values and run workloads
```bash
service cassandra stop   # startup cassandra server
vim /etc/cassandra.yaml  # change the parameter values
service cassandra start  # shutdown cassandra server
# check if the parameter value is correctly changed
cqlsh> SELECT * FROM system_views.settings where name='xx';

## run the workloads ##
# A: nosqlbench
./nb run driver=cql workload=cql-tabular tags=phase:rampup cycles=100k threads=4x waitmillis=10  cycles=100000  --classic-histograms prefix

# B: tlp-stress
./tlp-stress run RandomPartitionAccess --workload.rows=500000 --workload.select=partition -d 2h -p 10k --populate 20m field.random_access.value='random(4,8)' --csv > /dev/null 2>&1 &

# C: cassandra-stress
./cassandra-stress user profile=batch_too_large.yaml ops\(insert=1,query=1\) n=100000 -insert

# wait for a while and repeat above steps.
```

# Results for PostgreSQL
### 22 parameters missed by state-of-the-art tool, but have significant performance impact

| Rank      | Parameter | Is given by HotStrage 20 | workload       | perf. Before change | perf. After change | Metric         | perf. change rate (Impact) |
|-----------|--------------------------------------------------------------|--------------------------|----------------|---------------------|--------------------|----------------|----------------------------|
| rank-1    | `enable_sort`                                                  | no                       | TPCH(query_17) | 19.1                | 279.5              | execution time | 1363.4%                    |
| rank-2    | `enable_nestloop`                                              | no                       | TPCH(query_2)  | 8.14                | 51.71              | execution time | 535.3%                     |
| rank-3    | `enable_indexscan`                                             | no                       | TPCH(query_13) | 8.48                | 30.77              | execution time | 262.9%                     |
| rank-4    | `enable_partitionwise_aggregate`                               | no                       | TPCH(query_19) | 9.23                | 32.37              | execution time | 250.7%                     |
| rank-5    | `seq_page_cost`                                                | no                       | TPCH(query_2)  | 8.71                | 20.8               | execution time | 138.8%                     |
| rank-6    | `enable_hashjoin`                                              | no                       | TPCH(query_2)  | 8.26                | 19.02              | execution time | 130.3%                     |
| rank-7    | `enable_bitmapscan`                                            | no                       | TPCH(query_2)  | 8.37                | 19.26              | execution time | 130.1%                     |
| rank-8    | `full_page_writes`                                             | no                       | TPCC           | 0.99                | 2.23               | mean latency   | 125.3%                     |
| rank-9    | `enable_gathermerge`                                           | no                       | TPCH(query_13) | 30.91               | 61.16              | execution time | 97.9%                      |
| rank-10   | `enable_hashagg`                                               | no                       | TPCH(query_1)  | 24.2                | 42.1               | execution time | 74.0%                      |
| rank-11   | `synchronous_commit`                                           | no                       | TPCC           | 0.99                | 1.72               | mean latency   | 73.7%                      |
| rank-12   | `fsync`                                                        | __YES__                      | TPCC           | 220                 | 380                | throughput     | 72.7%                      |
| rank-13   | `join_collapse_limit`                                          | no                       | TPCH(query_21) | 31.17               | 48.16              | execution time | 54.5%                      |
| rank-14   | `enable_partition_pruning`                                     | no                       | TPCH(query_20) | 38.59               | 58.08              | execution time | 50.5%                      |
| rank-15   | `enable_seqscan`                                               | no                       | TPCH(query_1)  | 24.1                | 35.76              | execution time | 48.4%                      |
| rank-16   | `wal_sync_method`                                              | __YES__                      | TPCC           | 0.99                | 1.43               | mean latency   | 44.4%                      |
| rank-17   | `work_mem`                                                     | __YES__                      | TPCC           | 2.21                | 3.15               | throughput     | 42.5%                      |
| rank-18   | `force_parallel_mode`                                          | no                       | TPCH(query_20) | 40.65               | 57.55              | execution time | 41.6%                      |
| rank-19   | `wal_recycle`                                                  | no                       | TPCC           | 1758.83             | 2440.78            | throughput     | 38.8%                      |
| rank-20   | `temp_buffers`                                                 | __YES__                      | TPCC           | 4.42                | 6.03               | throughput     | 36.4%                      |
| rank-21   | `max_worker_processes`                                         | no                       | TPCC           | 407.62              | 548.07             | throughput     | 34.5%                      |
| rank-22   | `parallel_leader_participation`                                | no                       | TPCH(query_1)  | 26.89               | 36.02              | execution time | 34.0%                      |
| rank-23   | `enable_parallel_hash`                                         | no                       | TPCH(query_8)  | 26.9                | 34.96              | execution time | 30.0%                      |
| rank-24   | `jit`                                                          | no                       | TPCH(query_19) | 8.97                | 11.25              | execution time | 25.4%                      |
| rank-25   | `shared_buffers`                                               | __YES__                      | TPCC           | 3.45                | 4.31               | throughput     | 24.9% `                     |
| rank-26   | `max_wal_size`                                                 | __YES__                      | TPCC           | 0.835               | 1.03               | mean latency   | 23.4%                      |
| rank-27   | `effective_io_concurrency`                                     | __YES__                      | TPCC           | 0.9                 | 1.05               | mean latency   | 16.7%                      |
| rank-28   | `wal_compression`                                              | no                       | TPCC           | 179.57              | 204.67             | throughput     | 14.0%                      |
| rank-29   | `maintenance_work_mem`                                         | __YES__                      | TPCC           | 4.55                | 5.12               | throughput     | 12.5%                      |
| rank-30   | `max_parallel_workers`                                         | no                       | TPCC           | 176.2               | 198.23             | throughput     | 12.5%                      |
| NO impact | `wal_writer_delay`                                             | __YES__                      | TPCC           | 182.264             | 198.99             | throughput     | <10%                       |
| NO impact | `commit_delay`                                                 | __YES__                      | TPCC           | 4.82                | 5.21               | throughput     | <10%                       |
| NO impact | `effective_cache_size`                                         | __YES__                      | TPCC           | 533                 | 585                | throughput     | <10%                       |
| NO impact | `default_statistics_target`                                    | __YES__                      | TPCH(query_3)  | 30.72               | 32.82              | execution time | <10%                       |
| NO impact | `backend_flush_after`                                          | __YES__                      | TPCC           | 0.99                | 1.05               | mean latency   | <10%                       |
| NO impact | `wal_writer_flush_after`                                       | __YES__                      | TPCC           | 414.68              | 433.79             | throughput     | <10%                       |
| NO impact | `bgwriter_flush_after`                                         | __YES__                      | TPCC           | 543                 | 566                | throughput     | <10%                       |
| NO impact | `wal_buffers`                                                  | __YES__                      | TPCC           | 534                 | 551                | throughput     | <10%                       |
| NO impact | `max_parallel_workers_per_gather`                              | __YES__                      | TPCC           | 69824               | 70189              | throughput     | <10%                       |

| Perf-related   Groud Truth (127) -SafeTune | HotStorage (17) | Missed By SafeTune (34) |
|:------------------------------------------:|:---------------:|:-----------------------:|
|           `allow_system_table_mods`          |                 |                         |
|                `archive_mode`                |                 |                         |
|                 `autovacuum`                 |                 |                         |
|       `autovacuum_analyze_scale_factor`      |                 |            FN           |
|        `autovacuum_analyze_threshold`        |                 |            FN           |
|           `autovacuum_max_workers`           |                 |                         |
|        `autovacuum_vacuum_cost_limit`        |                 |                         |
|       `autovacuum_vacuum_scale_factor`       |                 |            FN           |
|         `autovacuum_vacuum_threshold`        |                 |                         |
|             `autovacuum_work_mem`            |                 |                         |
|             `backend_flush_after`            |       YES       |                         |
|            `bgwriter_flush_after`            |       YES       |                         |
|            `bgwriter_lru_maxpages`           |                 |                         |
|           `bgwriter_lru_multiplier`          |                 |            FN           |
|            `check_function_bodies`           |                 |                         |
|        `checkpoint_completion_target`        |                 |            FN           |
|           `checkpoint_flush_after`           |                 |                         |
|             `client_min_messages`            |                 |                         |
|                `commit_delay`                |       YES       |                         |
|               `commit_siblings`              |                 |                         |
|            `constraint_exclusion`            |                 |            FN           |
|            `cpu_index_tuple_cost`            |                 |                         |
|              `cpu_operator_cost`             |                 |            FN           |
|               `cpu_tuple_cost`               |                 |            FN           |
|               `data_sync_retry`              |                 |                         |
|             `debug_pretty_print`             |                 |                         |
|              `debug_print_parse`             |                 |            FN           |
|              `debug_print_plan`              |                 |                         |
|            `debug_print_rewritten`           |                 |                         |
|          `default_statistics_target`         |       YES       |            FN           |
|        `default_transaction_isolation`       |                 |                         |
|         `dynamic_shared_memory_type`         |                 |            FN           |
|            `effective_cache_size`            |       YES       |                         |
|          `effective_io_concurrency`          |       YES       |                         |
|              `enable_bitmapscan`             |                 |                         |
|             `enable_gathermerge`             |                 |                         |
|               `enable_hashagg`               |                 |                         |
|               `enable_hashjoin`              |                 |                         |
|            `enable_indexonlyscan`            |                 |            FN           |
|              `enable_indexscan`              |                 |                         |
|               `enable_material`              |                 |            FN           |
|              `enable_mergejoin`              |                 |            FN           |
|               `enable_nestloop`              |                 |                         |
|            `enable_parallel_hash`            |                 |                         |
|          `enable_partition_pruning`          |                 |                         |
|       `enable_partitionwise_aggregate`       |                 |                         |
|               `enable_seqscan`               |                 |            FN           |
|                 `enable_sort`                |                 |                         |
|               `enable_tidscan`               |                 |                         |
|            `escape_string_warning`           |                 |            FN           |
|             `force_parallel_mode`            |                 |                         |
|             `from_collapse_limit`            |                 |                         |
|                    `fsync`                   |       YES       |                         |
|              `full_page_writes`              |                 |                         |
|                    `geqo`                    |                 |                         |
|                 `geqo_effort`                |                 |                         |
|              `geqo_generations`              |                 |                         |
|               `geqo_pool_size`               |                 |            FN           |
|               `geqo_threshold`               |                 |                         |
|           `gin_pending_list_limit`           |                 |            FN           |
|            `hot_standby_feedback`            |                 |                         |
|                 `huge_pages`                 |                 |                         |
|                     `jit`                    |                 |                         |
|             `join_collapse_limit`            |                 |                         |
|               `log_checkpoints`              |                 |            FN           |
|               `log_connections`              |                 |                         |
|             `log_disconnections`             |                 |                         |
|             `log_error_verbosity`            |                 |                         |
|             `log_executor_stats`             |                 |                         |
|                `log_hostname`                |                 |            FN           |
|              `log_parser_stats`              |                 |            FN           |
|              `log_planner_stats`             |                 |            FN           |
|          `log_replication_commands`          |                 |                         |
|                `log_statement`               |                 |                         |
|             `log_statement_stats`            |                 |                         |
|              `logging_collector`             |                 |                         |
|            `maintenance_work_mem`            |       YES       |                         |
|               `max_connections`              |                 |                         |
|            `max_files_per_process`           |                 |            FN           |
|       `max_logical_replication_workers`      |                 |                         |
|            `max_parallel_workers`            |                 |                         |
|       `max_parallel_workers_per_gather`      |       YES       |                         |
|          `max_prepared_transactions`         |                 |                         |
|               `max_stack_depth`              |                 |            FN           |
|      `max_sync_workers_per_subscription`     |                 |                         |
|               `max_wal_senders`              |                 |                         |
|                `max_wal_size`                |       YES       |                         |
|            `max_worker_processes`            |                 |                         |
|        `parallel_leader_participation`       |                 |                         |
|             `parallel_setup_cost`            |                 |                         |
|             `parallel_tuple_cost`            |                 |            FN           |
|              `random_page_cost`              |                 |            FN           |
|                `seq_page_cost`               |                 |                         |
|               `shared_buffers`               |       YES       |                         |
|                     `ssl`                    |                 |                         |
|               `ssl_ecdh_curve`               |                 |                         |
|       `superuser_reserved_connections`       |                 |                         |
|            `synchronize_seqscans`            |                 |            FN           |
|             `synchronous_commit`             |                 |                         |
|            `syslog_split_messages`           |                 |                         |
|                `temp_buffers`                |       YES       |                         |
|               `temp_file_limit`              |                 |                         |
|                `trace_notify`                |                 |                         |
|           `trace_recovery_messages`          |                 |                         |
|                 `trace_sort`                 |                 |            FN           |
|              `track_activities`              |                 |            FN           |
|          `track_activity_query_size`         |                 |            FN           |
|           `track_commit_timestamp`           |                 |                         |
|                `track_counts`                |                 |                         |
|               `track_functions`              |                 |                         |
|               `track_io_timing`              |                 |                         |
|              `vacuum_cost_limit`             |                 |            FN           |
|           `vacuum_cost_page_dirty`           |                 |                         |
|            `vacuum_cost_page_hit`            |                 |            FN           |
|            `vacuum_cost_page_miss`           |                 |                         |
|          `vacuum_defer_cleanup_age`          |                 |                         |
|                 `wal_buffers`                |       YES       |                         |
|               `wal_compression`              |                 |                         |
|          `wal_consistency_checking`          |                 |                         |
|              `wal_keep_segments`             |                 |            FN           |
|                  `wal_level`                 |                 |                         |
|                `wal_log_hints`               |                 |                         |
|            `wal_receiver_timeout`            |                 |            FN           |
|               `wal_sync_method`              |       YES       |                         |
|              `wal_writer_delay`              |       YES       |                         |
|           `wal_writer_flush_after`           |       YES       |                         |
|                  `work_mem`                  |       YES       |                         |

# Result for Cassandra
### 26 parameters missed by state-of-the-art tool, but have significant performance impact


| Rank      | Parameter                                          | Is given by HotStrage 20 | workload            | perf.Before       change | perf.After       change | Metric                         | perf.change      rate (Impact) |
|-----------|----------------------------------------------------|--------------------------|---------------------|--------------------------|-------------------------|--------------------------------|--------------------------------|
| rank-1    | `native_transport_max_concurrent_connections`        | no                       | tlp-stress.KV       | 98.1                     | 1320.67                 | tail latency(99.9%)            | 1246%                          |
| rank-2    | `hinted_handoff_throttle_in_kb`                      | no                       | tlp-stress.KV       | 337.15                   | 2258.3                  | tail latency(100%)             | 570%                           |
| rank-3    | `max_hints_delivery_threads`                         | no                       | ca-stress           | 98.1                     | 284.25                  | tail latency(99.9%)            | 190%                           |
| rank-4    | `enable_user_defined_functions`                      | no                       | cql-tabular(insert) | 273.8                    | 564.3                   | excute maxtime（microseconds） | 106%                           |
| rank-5    | `prepared_statements_cache_size_mb`                  | no                       | cql-tabular(insert) | 564.3                    | 1113.62                 | excute maxtime（microseconds） | 97%                            |
| rank-6    | `concurrent_materialized_view_writes`                | no                       | cql-tabular(insert) | 286.12                   | 564.3                   | excute maxtime（microseconds） | 97%                            |
| rank-7    | `concurrent_writes`                                  | no                       | tlp-stress.KV       | 11.17                    | 20.56                   | mean latency(Writes)           | 84%                            |
| rank-8    | `dynamic_snitch_update_interval_in_ms`               | no                       | tlp-stress.KV       | 11.17                    | 18.69                   | mean latency(Writes)           | 67%                            |
| rank-9    | `row_cache_keys_to_save`                             | no                       | tlp-stress.KV       | 11.97                    | 19.78                   | mean latency(Reads)            | 65%                            |
| rank-10   | `row_cache_size_in_mb`                               | __YES__                      | tlp-stress.KV       | 11.17                    | 18.4                    | mean latency(Writes)           | 65%                            |
| rank-11   | `snapshot_before_compaction`                         | no                       | tlp-stress.KV       | 11.97                    | 19.59                   | mean latency(Reads)            | 64%                            |
| rank-12   | `commitlog_total_space_in_mb`                        | no                       | tlp-stress.KV       | 11.17                    | 18.28                   | mean latency(Writes)           | 64%                            |
| rank-13   | `inter_dc_tcp_nodelay`                               | no                       | tlp-stress.KV       | 11.97                    | 19.52                   | mean latency(Reads)            | 63%                            |
| rank-14   | `cdc_free_space_check_interval_ms`                   | no                       | tlp-stress.KV       | 11.17                    | 18.16                   | mean latency(Writes)           | 63%                            |
| rank-15   | `memtable_flush_writers`                             | no                       | tlp-stress.KV       | 11.17                    | 17.96                   | mean latency(Writes)           | 61%                            |
| rank-16   | `file_cache_size_in_mb`                              | __YES__                      | tlp-stress.KV       | 11.97                    | 19.21                   | mean latency(Reads)            | 60%                            |
| rank-17   | `credentials_update_interval_in_ms`                  | no                       | tlp-stress.KV       | 11.17                    | 17.43                   | mean latency(Writes)           | 56%                            |
| rank-18   | `hints_flush_period_in_ms`                           | no                       | tlp-stress.KV       | 11.97                    | 18.56                   | mean latency(Reads)            | 55%                            |
| rank-19   | `index_summary_capacity_in_mb`                       | no                       | tlp-stress.KV       | 11.97                    | 18.54                   | mean latency(Reads)            | 55%                            |
| rank-20   | `commitlog_segment_size_in_mb`                       | __YES__                      | tlp-stress.KV       | 11.97                    | 18.52                   | mean latency(Reads)            | 55%                            |
| rank-21   | `compaction_large_partition_warning_threshold_mb`    | no                       | tlp-stress.KV       | 11.17                    | 17.16                   | mean latency(Writes)           | 54%                            |
| rank-22   | `internode_compression`                              | no                       | tlp-stress.KV       | 11.17                    | 16.95                   | mean latency(Writes)           | 52%                            |
| rank-23   | `counter_cache_size_in_mb`                           | __YES__                      | tlp-stress.KV       | 11.97                    | 17.96                   | mean latency(Reads)            | 50%                            |
| rank-24   | `gc_warn_threshold_in_ms`                            | no                       | tlp-stress.KV       | 11.17                    | 16.74                   | mean latency(Writes)           | 50%                            |
| rank-25   | `compaction_throughput_mb_per_sec`                   | __YES__                      | tlp-stress.KV       | 11.97                    | 17.67                   | mean latency(Reads)            | 48%                            |
| rank-26   | `ideal_consistency_level`                            | no                       | tlp-stress.KV       | 11.97                    | 17.57                   | mean latency(Reads)            | 47%                            |
| rank-27   | `roles_update_interval_in_ms`                        | no                       | tlp-stress.KV       | 11.97                    | 17.41                   | mean latency(Reads)            | 45%                            |
| rank-28   | `column_index_cache_size_in_kb`                      | __YES__                      | tlp-stress.KV       | 11.17                    | 16.21                   | mean latency(Writes)           | 45%                            |
| rank-29   | `auto_snapshot`                                      | no                       | tlp-stress.KV       | 11.97                    | 17.35                   | mean latency(Reads)            | 45%                            |
| rank-30   | `key_cache_save_period`                              | __YES__                      | tlp-stress.KV       | 11.97                    | 15.8                    | mean latency(Reads)            | 32%                            |
| rank-31   | `memtable_cleanup_threshold`                         | __YES__                      | tlp-stress.KV       | 11.17                    | 14.64                   | mean latency(Writes)           | 31%                            |
| rank-32   | `key_cache_keys_to_save`                             | no                       | tlp-stress.KV       | 11.17                    | 14.37                   | mean latency(Writes)           | 29%                            |
| rank-33   | `otc_coalescing_enough_coalesced_messages`           | no                       | tlp-stress.KV       | 11.17                    | 14.19                   | mean latency(Writes)           | 27%                            |
| rank-34   | `key_cache_size_in_mb`                               | __YES__                      | tlp-stress.KV       | 11.17                    | 13.07                   | mean latency(Writes)           | 17%                            |
| rank-35   | `allocate_tokens_for_keyspace`                       | no                       | cql-tabular(insert) | 483.6                    | 564.3                   | excute maxtime（microseconds） | 17%                            |
| rank-36   | `native_transport_max_threads`                       | __YES__                      | tlp-stress.KV       | 11.97                    | 13.88                   | mean latency(Reads)            | 16%                            |
| NO impact | `column_index_size_in_kb`                            | no                       | cql-tabular(insert) | 564.3                    | 313.94                  | excute maxtime（microseconds） | <10%                           |
| NO impact | `batchlog_replay_throttle_in_kb`                     | no                       | cql-tabular(insert) | 564.3                    | 316.3                   | excute maxtime（microseconds） | <10%                           |
| NO impact | `gc_log_threshold_in_ms`                             | no                       | tlp-stress.KV       | 11.17                    | 16.04                   | mean latency(Writes)           | <10%                           |
| NO impact | `counter_cache_keys_to_save`                         | no                       | cql-tabular(insert) | 564.3                    | 322.88                  | excute maxtime（microseconds） | <10%                           |
| NO impact | `concurrent_reads`                                   | __YES__                      | tlp-stress.KV       | 11.97                    | 17.03                   | mean latency(Reads)            | <10%                           |
| NO impact | `credentials_validity_in_ms`                         | no                       | tlp-stress.KV       | 11.17                    | 15.38                   | mean latency(Writes)           | <10%                           |
| NO impact | `counter_cache_save_period`                          | __YES__                      | tlp-stress.KV       | 11.17                    | 15.19                   | mean latency(Writes)           | <10%                           |
| NO impact | `native_transport_max_concurrent_connections_per_ip` | no                       | tlp-stress.KV       | 11.97                    | 16.26                   | mean latency(Reads)            | <10%                           |
| NO impact | `trickle_fsync`                                      | no                       | tlp-stress.KV       | 11.17                    | 15.12                   | mean latency(Writes)           | <10%                           |
| NO impact | `concurrent_compactors`                              | __YES__                      | tlp-stress.KV       | 11.97                    | 16.12                   | mean latency(Reads)            | <10%                           |
| NO impact | `back_pressure_enabled`                              | no                       | tlp-stress.KV       | 11.17                    | 14.76                   | mean latency(Writes)           | <10%                           |
| NO impact | `memtable_heap_space_in_mb`                          | __YES__                      | tlp-stress.KV       | 11.17                    | 14.42                   | mean latency(Writes)           | <10%                           |
| NO impact | `row_cache_save_period`                              | __YES__                      | tlp-stress.KV       | 11.97                    | 14.03                   | mean latency(Reads)            | <10%                           |
| NO impact | `batch_size_warn_threshold_in_kb`                    | no                       | cql-tabular(insert) | 564.3                    | 623.86                  | excute maxtime（microseconds） | <10%                           |

|      Perf-related   Groud Truth (64) -SafeTune     | HotStorage (15) | Missed By SafeTune (11) |
|:--------------------------------------------------:|:---------------:|:-----------------------:|
|            `allocate_tokens_for_keyspace`            |                 |                         |
|                    `auto_snapshot`                   |                 |                         |
|                `back_pressure_enabled`               |                 |                         |
|           `batch_size_warn_threshold_in_kb`          |                 |                         |
|           `batchlog_replay_throttle_in_kb`           |                 |                         |
|          `cdc_free_space_check_interval_ms`          |                 |                         |
|            `column_index_cache_size_in_kb`           |       YES       |            FN           |
|               `column_index_size_in_kb`              |                 |                         |
|                `commit_failure_policy`               |                 |                         |
|                `commitlog_compression`               |                 |            FN           |
|            `commitlog_segment_size_in_mb`            |       YES       |            FN           |
|                   `commitlog_sync`                   |                 |            FN           |
|             `commitlog_total_space_in_mb`            |                 |                         |
|   `compaction_large_partition_warning_threshold_mb`  |                 |            FN           |
|          `compaction_throughput_mb_per_sec`          |       YES       |                         |
|                `concurrent_compactors`               |       YES       |            FN           |
|         `concurrent_materialized_view_writes`        |                 |                         |
|                  `concurrent_reads`                  |       YES       |            FN           |
|                  `concurrent_writes`                 |                 |                         |
|             `counter_cache_keys_to_save`             |                 |                         |
|              `counter_cache_save_period`             |       YES       |            FN           |
|              `counter_cache_size_in_mb`              |       YES       |                         |
|          `credentials_update_interval_in_ms`         |                 |                         |
|             `credentials_validity_in_ms`             |                 |                         |
|                 `cross_node_timeout`                 |                 |                         |
|         `dynamic_snitch_reset_interval_in_ms`        |                 |                         |
|        `dynamic_snitch_update_interval_in_ms`        |                 |                         |
|            `enable_user_defined_functions`           |                 |                         |
|                `file_cache_size_in_mb`               |       YES       |                         |
|               `gc_log_threshold_in_ms`               |                 |                         |
|               `gc_warn_threshold_in_ms`              |                 |                         |
|               `hinted_handoff_enabled`               |                 |                         |
|            `hinted_handoff_throttle_in_kb`           |                 |                         |
|                  `hints_compression`                 |                 |            FN           |
|              `hints_flush_period_in_ms`              |                 |                         |
|               `ideal_consistency_level`              |                 |                         |
|            `index_summary_capacity_in_mb`            |                 |                         |
|      `index_summary_resize_interval_in_minutes`      |                 |                         |
|                `inter_dc_tcp_nodelay`                |                 |                         |
|                `internode_compression`               |                 |                         |
|               `key_cache_keys_to_save`               |                 |                         |
|                `key_cache_save_period`               |       YES       |                         |
|                `key_cache_size_in_mb`                |       YES       |                         |
|             `max_hints_delivery_threads`             |                 |                         |
|              `memtable_allocation_type`              |                 |                         |
|             `memtable_cleanup_threshold`             |       YES       |                         |
|               `memtable_flush_writers`               |                 |                         |
|              `memtable_heap_space_in_mb`             |       YES       |                         |
|     `native_transport_max_concurrent_connections`    |                 |                         |
| `native_transport_max_concurrent_connections_per_ip` |                 |                         |
|            `native_transport_max_threads`            |       YES       |                         |
|              `native_transport_port_ssl`             |                 |            FN           |
|      `otc_coalescing_enough_coalesced_messages`      |                 |                         |
|             `permissions_validity_in_ms`             |                 |                         |
|          `prepared_statements_cache_size_mb`         |                 |                         |
|             `roles_update_interval_in_ms`            |                 |                         |
|                `roles_validity_in_ms`                |                 |                         |
|               `row_cache_keys_to_save`               |                 |                         |
|                `row_cache_save_period`               |       YES       |            FN           |
|                `row_cache_size_in_mb`                |       YES       |                         |
|             `snapshot_before_compaction`             |                 |                         |
|       `sstable_preemptive_open_interval_in_mb`       |                 |                         |
|         `transparent_data_encryption_options`        |                 |                         |
|                    `trickle_fsync`                   |                 |                         |

# How we got the result

We also open up all our inital testing result in `raw_test_data`, which contains all testing result in raw format, we analyze them and make them into one table shown above.