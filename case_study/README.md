# __Case Study__ (the other four cases)

This page shows that the other four cases that are not present in the paper due to the limited space

## Configuration by __OtterTune__ in MySQL
```
innodb_buffer_pool_size         128M  -> 16.4G
key_buffer_size                 8M    -> 32M
innodb_thread_sleep_delay       10000 -> 0
innodb_flush_method             fsync -> O_DIRECT
innodb_log_file_size            48M   -> 4.1G
innodb_thread_concurrency       0     -> 1024
innodb_doublewrite              1     -> 0
performance_schema              on    -> off
innodb_read_ahead_threshold     56    -> 41
innodb_flush_log_at_trx_commit  1     -> 0
...
```

## __Side-effects__ in MySQL

Side-effect identified by __SafeTune__, we triggered consequences (if not warned about).

### __CASE 5__
  - Parameter: `innodb_flush_log_at_trx_commit`
  - Side-effect： ___Lower reliability___
  - Observation:

    __OtterTune__ turns `innodb_flush_log_at_trx_commit` from `1` to `0`, affecting reliability:
    ```
    mysql> INSERT INTO t SELECT now();
    ```
    Simulate a power loss. 
    ```
    killall -9 mysqld
    ```
    There should be `empty set`(data loss) after `SELECT * FROM t;`, but we still observe the right value.
    Since setting `innodb_flush_log_at_trx_commit = 0`, there is not a guaranteed data loss. As documented:

    > With a setting of 0, logs are written and flushed to disk once __per second__. Transactions for which logs have not been flushed can be lost in a crash. 
    
    So we repeat the steps above repeatedly to find the proper timing that trigger a data loss. As documented: 
    Finally we trigger the data loss by increasing the data inserted and using a script to kill the server:
    ```bash
    i=0;
    while true;
    do mysql test -e "INSERT INTO t SELECT now()";
      # insert 100 records into the table (innodb_flush_log_at_trx_commit = 0), it is expected
      # that these happens within one second. Thus, these transactions have not been synced.
        if [ $i -eq 100 ]; 
            then killall -9 mysqld; # after 100 records, powerloss!
            sleep 1;
        fi;
        # before power loss, we can observe normal data insertion.
        mysql test -e "INSERT count(*) FROM t" >> data-loss.log;
        # after power loss, inserts continues, but data before power loss may be lossed.
        if [ $i -gt 110 ];
            then break;
        fi;
        ((++i));
    done
    ```
    Triggered data loss, content of `data-loss.log`:  
    ```
    ...
    99
    100
    101
    102
    103
    3   <---- 100 records loss!
    4
    5
    ...
    ```
    Setting `innodb_flush_log_at_trx_commit` = `1`, content of `data-loss.log` (i.e., NO data loss):
    ```
    ...
    99
    100
    101
    102
    103
    104
    ...
    ```

### __CASE 6__
  - Parameter: Parameter: `innodb_doublewrite`
  - Side-effect: ___Reduced reliablity___
  - Observation:
  - As documented, it causes reliability issue under some conditions (bolded text):

    > When enabled (the default), InnoDB stores all data twice, first to the doublewrite buffer, then to the actual data files. This variable can be turned off for cases when top performance is needed __rather than concern for data integrity or possible failures__.
    
    We mount the `Ext4` filesystem __without__ `data`=`journal` mounting option,
    then, we startup MySQL and with `innodb_doublewrite` = `0`:
    ```
    mount -o data=writeback /dev/sda /mnt/data
    mysqld_safe --innodb_doublewrite=0 &
    ```
    Next, we do a lot write-intensive workload:
    ```
    ./tpcc_run
    ```
    And simulate a power loss:
    ```
    killall -9 mysqld
    ```
    Then restart MySQL and we observe the following:
    ```
    ...
    InnoDB: Database page corruption on disk or a failed  <===== DATA CORRUPTION
    InnoDB: file read of page 13479.
    InnoDB: You may have to recover from a backup.
    ...
    ```
  - a interesting thing is that tuning this parameter for performance is [__strictly forbidden__ in Oracle DB](https://community.oracle.com/tech/developers/discussion/1087650/how-oracle-prevent-partial-write)
  - this data corruption never happens when `innodb_doublewrite` = `1`


## Configuration by __OtterTune__ in PostgreSQL
```
fsync                           on    -> off
shared_buffers                  128M  -> 18G
checkpoint_segments             3     -> 540
effective_cache_size            4G    -> 23G
max_wal_size                    1G    -> 12G
bgwriter_lru_maxpages           100   -> 1000
bgwriter_delay                  200ms -> 120ms
deadlock_timeout                1s    -> 2s
default_statistics_target       100	  -> 98
effective_io_concurrency        1     -> 8
max_worker_processes            8     -> 12
...
```
## __Side-effects__ in PostgreSQL
Side-effect identified by __SafeTune__, we triggered consequences (if not warned about).

### __CASE 7__
  - Parameter: `shared_buffers`
  - Side-effect: ___Higher cost___  

    Before tuning:
    ```bash
    top -p [postgresql-pid]
    PID   USER     PR NI VIRT   RES    SHR      %CPU %MEM COMMAND
    12589 postgres 20 0  1.231g 0.051g 0.01g  S 0.0  0.0  postgres
    ```
    OtterTune increases `shared_buffers` from `128M` to `18G`:
    ```bash
    top -p [postgresql-pid]
    PID   USER     PR NI VIRT    RES    SHR      %CPU %MEM COMMAND
    25882 postgres 20 0  21.331g 1.829g 0.01g  S 0.0  1.4  postgres
                          \_____ 
                                  Higher Cost (Memory)
    ```
### __CASE 8__: 
  - Parameter: `max_worker_processes`
  - Side-effect: ___Higher cost___  

    Before tuning, run workload and monitor
    ```
    ./tpcc_run &
    top -p [postgresql-pid]

    PID   USER     PR NI VIRT   RES    SHR      %CPU   %MEM COMMAND
    8937  postgres 20 0  1.231g 0.051g 0.01g  S 283.5  0.0  postgres
    8937  postgres 20 0  1.232g 0.051g 0.01g  S 295.2  0.0  postgres
    8937  postgres 20 0  1.234g 0.053g 0.01g  S 215.8  0.0  postgres

    ```
    OtterTune increases `max_worker_processes` from `8` to `12`, run workload and monitor
    ```
    ./tpcc_run
    top -p [postgresql-pid]

    PID   USER     PR NI VIRT    RES    SHR      %CPU %MEM COMMAND
    11290 postgres 20 0  1.233g  0.066g 0.01g  S 325.8  1.4  postgres
    11290 postgres 20 0  1.233g  0.066g 0.01g  S 289.2  1.4  postgres
    11290 postgres 20 0  1.234g  0.067g 0.01g  S 303.1  1.4  postgres
                                                    \_____ 
                                                          Higher Cost (CPU)
    ```

## Other things

 __OtterTune__ does not touch the parameters (e.g., `ssl`) who gain performance by sacrificing ___security___ in both software. Thus, __SafeTune__ does not warn about side-effects of "___Reduced security___".
