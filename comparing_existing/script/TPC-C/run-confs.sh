
DEVICES=(hdd-sas-dell sata-s4510)
TIME=100 # seconds to run the benchmark for each test. 10 sec per measure.
workload_prefix="/dir/to/sysbench-tpcc/"

kill_pgsql(){
	res="$(ps aux | grep postgres)"
	arrRES=(${res// /;})
	if [ "${arrRES[1]}" = "" ]; then
		echo "    \_____"
		echo '           No PostgresSQL via ps, OK.'
	else
		for psLine in ${arrRES[@]}; do
			arr_psLine=(${psLine//;/ })
			echo "${arr_psLine[1]}, <${arr_psLine[10]} ${arr_psLine[11]}> killed by -9"
			echo "123" | sudo -S kill -9 ${arr_psLine[1]}
		done
		echo "123" | sudo -S rm -f /var/run/postgresql/.s.PGSQL.5432
		echo "123" | sudo -S rm -f /var/run/postgresql/.s.PGSQL.5432.lock
	fi
}


run(){

	for(( i=0;i<${#conf_value[@]};i++)); do

		echo "[configuration]: ${conf_name}=${conf_value[i]}"
		echo ""

		for DEV in ${DEVICES[@]}; do

			echo "[device]: $DEV"

			# 1. shutdown if exist AGAIN
			echo ">>>>>>>>> ps/kill: making sure no PostgresSQL is runnning and no socket is available."
			kill_pgsql
			sleep 1

			# 2. startup postgreSQL
			echo ""
			echo ">>>>>>>>> NOW, startup PostgreSQL..."
			cd /usr/lib/postgresql/12/bin
			echo "123" | sudo -S -u postgres ./pg_ctl start -D /mnt/${DEV}/postgresql-data -o "-c ${conf_name}=${conf_value[i]} ${OTHER_CONFS}" -w
			#echo "123" | sudo -S -u postgres ./pg_ctl start -D /mnt/${DEV}/postgresql-data -o "-c fsync=off -c wal_sync_method=fdatasync -c synchronous_commit=off -c full_page_writes=off" -w
			sleep 2
			PING="$(ls -a /var/run/postgresql/ | grep -x .s.PGSQL.5432)"
			if [ "$PING" = ".s.PGSQL.5432" ]; then echo ">>>>>>>>> PostgreSQL is up by /var/run/postgresql/.s.PGSQL.5432"; else echo "Startup FAILED! Exit" && echo "" && exit; fi

			# 3. cleanup
			echo ""
			echo ">>>>>>>>> Cleanning OS cache and TRIM fs"
			echo "123" | sudo -S /sbin/sysctl vm.drop_caches=3
			echo "123" | sudo -S fstrim -v /mnt/${DEV}

			# 4. run TPC-C workload
			cd ${workload_prefix}
			echo ""
			echo ">>>>>>>>> TPCC workload RUN!" && sleep 20
			./tpcc.lua --tables=10 --scale=100 --pgsql-user=postgres --pgsql-db=postgres --db-driver=pgsql --threads=8 --time=${TIME} --report-interval=10 run
			sleep 20

			# 5. shutdown if exist
			cd /usr/lib/postgresql/12/bin
			PING="$(ls -a /var/run/postgresql/ | grep -x .s.PGSQL.5432)"
			if [ "${PING}" = ".s.PGSQL.5432" ]; then echo "shutdown normally..." && echo "123" | sudo -S -u postgres ./pg_ctl stop -D /mnt/${DEV}/postgresql-data -w; else echo "/var/run/postgresql/.s.PGSQL.5432 not found, no need shutdown."; fi
			sleep 2

		done
	done

	echo ""
	echo "-------------------"
	echo "      FINISH!"
	echo "-------------------"

}


conf_name="shared_buffers"
conf_value=(128MB 4GB)
run
