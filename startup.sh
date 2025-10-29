export PYTHONPATH=$PYTHONPATH:$(pwd)
SPOTIFY_CONFIG_LOCATION=$(pwd)/src/app_config/app_config.cfg
export SPOTIFY_CONFIG_LOCATION
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
