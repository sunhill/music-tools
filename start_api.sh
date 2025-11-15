#!/bin/bash
# script that starts the FastAPI backend server
# check at http://localhost:8001/
set -e
SPOTIFY_CONFIG_LOCATION=$(pwd)/src/app_config/app_config.ini
export SPOTIFY_CONFIG_LOCATION
export PYTHONPATH=src

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
