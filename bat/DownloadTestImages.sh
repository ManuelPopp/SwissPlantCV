#!/usr/bin/env bash



cd "$(dirname "$0")"

cd ../py3/requests
python3 infoflora.py -out_dir "N:/prj/COMECO/img" -releve_table "standard"
read -p "Press any key to continue... " -n1 -s