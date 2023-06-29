#!/usr/bin/env bash
cd "$(dirname "$0")"
cd ../py3/requests
python3 batchrequest.py -releve_table "standard"
read -p "Press any key to continue... " -n1 -s