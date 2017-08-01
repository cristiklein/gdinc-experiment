#!/bin/bash

#
# Defaults
#
vms="vm-00 vm-01"

#
# Helper functions
#
function log {
	echo [`date --iso-8601=ns`] "$*" >&2
}
function cleanup {
	log "*** Cleanup ***"
	for vm in $vms; do
		docker rm -f httpmon-$vm || true
		rm -f /tmp/httpmon-$vm.fifo || true
	done
	while pkill -f resource-manager.py; do
		log "Killing resource-manager.py ..."
	done
}

#
# Main
#

# Die on any error
set -e

cd `dirname $0`

#
# Cleanup
#
cleanup
log "Waiting 10 seconds for system to settle ..."
sleep 10

#
# Startup
#

log "*** Starting ***"
for vm in $vms; do
	log "Starting httpmon for $vm"

	mkfifo /tmp/httpmon-$vm.fifo
	docker run -i --net=host --name httpmon-$vm cklein/httpmon --url "http://$vm/PHP/RandomItem.php" --concurrency 0 --timeout 30 --deterministic --dump < /tmp/httpmon-$vm.fifo &> httpmon-$vm.log &
done
python ../resource-manager.py &> resource-manager.log &

log "Generating workload BEGIN"
START=`date --iso-8601=ns`
START_FOR_DOCKER_LOGS=`date +%Y-%m-%dT%TZ --utc --date $START`
pids=""
for vm in $vms; do
	(
		echo "open=1"
		echo "thinktime=1"
		for load in `cat workloads/$vm.load`; do
			log "$vm: concurrency=$load"
			echo "concurrency=$load"
			sleep 5
		done
		echo "concurrency=0"
	) > /tmp/httpmon-$vm.fifo &
   	pids="$pids $!"
done
wait $pids
log "Generating workload END"

log "Gathering logs"
for vm in $vms; do
	docker --host tcp://$vm:2375 logs --since $START_FOR_DOCKER_LOGS --timestamps rubis-web-tier-0 > rubis-web-tier-$vm.log
done

#
# Cleanup
#
cleanup

