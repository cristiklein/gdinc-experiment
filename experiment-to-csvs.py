#!/usr/bin/env python
from __future__ import division, print_function

import argparse
import re
import shlex
import tarfile

parser = argparse.ArgumentParser(
        description='Extract CSVs for plotting from experiment TARs.')
parser.add_argument('experiment', help='the TAR file to extract experimental data from')

args = parser.parse_args()

with \
        open('concurrency.csv', 'w') as fConcurrency, \
        open('prices_vm-00.csv', 'w') as fPrices, \
        open('demand_vm-00.csv', 'w') as fDemand, \
        open('capacity_vm-00.csv', 'w') as fCapacity, \
        open('theta_vm-00.csv', 'w') as fTheta, \
        tarfile.open(args.experiment) as tar:
    for member in tar.getmembers():
        f = tar.extractfile(member)
        if member.name == 'httpmon-vm-00.log':
            print('time', 'concurrency', sep=',', file=fConcurrency)
            print('time', 'throughput', 'theta', sep=',', file=fTheta)
            for line in f.readlines():
                m = re.match('time=([0-9e.-]+).*concurrency=([0-9e.-]+)', line)
                if m:
                    print(m.group(1), m.group(2), sep=',', file=fConcurrency)

                m = re.match('time=([0-9e.-]+).*throughput=([0-9e.-]+)rps.*rr=([0-9e.-]+)', line)
                if m:
                    print(m.group(1), m.group(2), m.group(3), sep=',', file=fTheta)

        if member.name == 'resource-manager.log':
            print('time', 'p_b', 'p_d', sep=',', file=fPrices)
            print('time', 'c_b', 'c_d', sep=',', file=fDemand)
            print('time', 'c_i', sep=',', file=fCapacity)

            for line in f.readlines():
                m = re.match('([0-9e.-]+).*vm-00.*p_b=([0-9e.-]+).*p_d=([0-9e.-]+)', line)
                if m:
                    print(m.group(1), m.group(2), m.group(3), sep=',', file=fPrices)

                m = re.match("([0-9e.-]+).*vm-00.*c_b=([0-9e.-]+).*c_d=([0-9e.-]+)", line)
                if m:
                    print(m.group(1), m.group(2), m.group(3), sep=',', file=fDemand)

                m = re.match("([0-9e.-]+).*vm-00.*c_i=([0-9e.-]+)", line)
                if m:
                    print(m.group(1), m.group(2), sep=',', file=fCapacity)
