#!/usr/bin/env bash

cd "$(dirname "$0")"

cd ../py3/sampling
python3 completedreleves.py
read -p "Press any key to continue... " -n1 -s
