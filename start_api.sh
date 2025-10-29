#!/bin/bash
set -e
SPOTIFY_CONFIG_LOCATION=$(pwd)/src/app_config/app_config.ini
export SPOTIFY_CONFIG_LOCATION
export PYTHONPATH=src

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
