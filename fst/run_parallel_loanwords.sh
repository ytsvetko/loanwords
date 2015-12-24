#!/bin/bash

usage='
./run_parallel_loanwords.sh --ar_pronunciation_dict ../data/pron-dict/pron-dict.it \
                            --sw_pronunciation_dict ../data/pron-dict/pron-dict.mt \
                            --test_file ../data/train.en-mt-it \
                            --in_ot_constraint_weights weights/constraint_weights_init \
                            --remove_meta_arcs
'

NUM_CPUS=$(grep -c ^processor /proc/cpuinfo)
#FREE_MEM_KB=$(free|awk '/^Mem:/{print $4}')
#NEEDED_MEM_PER_WORKER_KB=1300000

let MAX_WORKERS=10
let NUM_WORKERS_CPU=NUM_CPUS
#let NUM_WORKERS_MEM=FREE_MEM_KB/NEEDED_MEM_PER_WORKER_KB
#NUM_WORKERS=$((${NUM_WORKERS_CPU}>${NUM_WORKERS_MEM}?${NUM_WORKERS_MEM}:${NUM_WORKERS_CPU}))
NUM_WORKERS=${NUM_WORKERS_CPU}
NUM_WORKERS=$((${NUM_WORKERS}>${MAX_WORKERS}?${MAX_WORKERS}:${NUM_WORKERS}))
echo "Using ${NUM_WORKERS} workers"

# Pre-initialize
nice ./loanwords.py "$@" --worker_id=-1 || { echo "Loanwords initialization failed" ; exit 1 ; }

let LAST_WORKER=NUM_WORKERS-1
for WORKER_ID in $(seq 0 ${LAST_WORKER}) ; do
  ./loanwords.py "$@" --num_workers=${NUM_WORKERS} --worker_id=${WORKER_ID} &
done

FAIL=0
for job in $(jobs -p) ; do
echo $job
  wait $job || let "FAIL+=1"
done

exit $FAIL
