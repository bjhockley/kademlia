#! /bin/bash
reset
clear
rm -rf ./cache.pickle
PYTHONPATH=. python examples/server.py  8881 8882 8883 2>&1 &
PYTHONPATH=. python examples/server.py  8882 8881 8883 2>&1 &
PYTHONPATH=. python examples/server.py  8883 8881 8882 2>&1 &


time PYTHONPATH=. python examples/benbenchmark.py  500

for pid in `ps aux | grep examples/server.py | grep -v grep | awk '{print $2}'`; do echo "stopping server at pid $pid" ; kill -INT $pid;  done

