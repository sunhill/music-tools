#!/bin/bash

# Exit on error
set -e

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

# Set environment variables
export SPOTIFY_CONFIG_LOCATION="src/app_config/app_config.ini"
export RUNNING_IN_DOCKER="False"
export PYTHONPATH="src"

# Run spotify-export
spotify-export

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
  deactivate
fi
