#!/usr/bin/env python
from __future__ import division, print_function

from itertools import islice

# The original trace contains 90 days of data and has a sampling interval of 5
# minutes. We trip the trace to 10 days and compress the sampling interval to 5
# seconds. Experiment duration should be 4 hours. :(

def main():
    RPS_PER_CORE_NON_DEGRADED=10 # profiled offline
    MAX_CAPACITY=30/3.03810674805*2 # around 30 cores
    MAX_IN_TIMESTEPS=2880
    IN_FILE='roles/client/files/workloads/cpu_usage_rnd_2013-7-8-9.csv'
    OUT_FILE='roles/client/files/workloads/vm-00.load'

    max_capacity = 0
    with open(IN_FILE) as fIn:
        for line in islice(fIn.readlines(), MAX_IN_TIMESTEPS):
            time, capacity = map(float, line.split(','))
            max_capacity = max(capacity, max_capacity)
    print('max_capacity:', max_capacity)

    scale_capacity_by = MAX_CAPACITY / max_capacity
    print('scale_capacity_by:', scale_capacity_by)

    scale_load_by = scale_capacity_by * RPS_PER_CORE_NON_DEGRADED
    print('scale_load_by:', scale_load_by)
    with open(IN_FILE) as fIn, open(OUT_FILE, 'w') as fOut:
        for line in islice(fIn.readlines(), MAX_IN_TIMESTEPS):
            time, load = map(float, line.split(','))
            print(load * scale_load_by, file=fOut)

if __name__=='__main__':
    main()
