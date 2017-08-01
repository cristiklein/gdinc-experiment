#!/bin/bash

cd `dirname $0`

START=`date --iso-8601=seconds`

./deploy.sh --tags update-experiment
ssh root@p18.ds.cs.umu.se gd_implementation/perform-single-exp.sh
ssh root@p18.ds.cs.umu.se 'cd gd_implementation; tar -cv *.log' > experiment-$START.tar
