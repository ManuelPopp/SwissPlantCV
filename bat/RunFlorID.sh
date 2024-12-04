#!/usr/bin/env bash
cd "$(dirname "$0")"
cd ../py3/florid_v001b
poetry run sanic main:app --workers 1 --dev --debug --host=0.0.0.0 --port=8000
pause