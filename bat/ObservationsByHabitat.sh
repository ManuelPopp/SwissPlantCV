#!/usr/bin/env bash

cd "$(dirname "$0")"
cd ../py3/sampling
python3 observationsbyhabitat.py
read -p "Press any key to continue... " -n1 -s
