#! /bin/bash

# Temporarily ignore "child process done" monitoring
set +m
pids=()
for replay in data/*.db
do
    # Background each task and track the PID so that we can wait for it to end
    (python3 dump-data.py --debug $replay ${replay/.db}.log >${replay/.db}.txt 2>&1 && echo "$replay completed successfully") &
    pids[${#pids[@]}]=$!
done 2>&1 | grep -v "^[\[0-9\]+]"  # Hide the "[n] PID" output

for pid in ${pids[*]}
do
    wait $pid
done

# Restore "child process done" monitoring
set -m