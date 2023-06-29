#!/usr/bin/env bash
cd "$(dirname "$0")"
cd ../py3/comeco
py predict.py -address 5001
pause