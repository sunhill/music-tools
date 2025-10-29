#!/bin/bash

# Exit on error
set -e

# Optional: activate virtual environment if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Optional: set environment variables (edit as needed)
export SPOTIFY_CONFIG_LOCATION="src/app_config/app_config.ini"
export RUNNING_IN_DOCKER="False"
export PYTHONPATH="src"

# Run the Python data extraction
python -m spotify.spotify_get_data

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
  source deactivate
fi