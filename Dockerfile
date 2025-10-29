FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /src

# Copy the requirements file into the container
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src /src/
COPY start_api.sh .

ENV PYTHONUNBUFFERED=1

# Set environment variables
ENV PYTHONPATH=./
ENV PYTHONPATH=$PYTHONPATH:/src
ENV SPOTIFY_CONFIG_LOCATION=/src/app_config/app_config.ini
# Command to run the application
#CMD ["fastapi", "run", "main.py", "--port", "8080" ]
RUN chmod +x start_api.sh
CMD ["/bin/bash","-c","./start_api.sh"]
#CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app"]