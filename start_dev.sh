#!/bin/bash

# Kill any existing processes on ports 8001 and 3000
lsof -i :8001 | awk 'NR!=1 {print $2}' | xargs kill -9 2>/dev/null
lsof -i :3000 | awk 'NR!=1 {print $2}' | xargs kill -9 2>/dev/null

# Function to handle cleanup on script exit
trap 'kill $(jobs -p)' EXIT

# Start the backend
SPOTIFY_CONFIG_LOCATION=$(pwd)/src/app_config/app_config.ini
export SPOTIFY_CONFIG_LOCATION
export PYTHONPATH=src
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &

# Start the frontend
#cd /Users/simon/dev/spotify-export/frontend
cd frontend || exit 1
npm start &

# Wait for both processes
wait