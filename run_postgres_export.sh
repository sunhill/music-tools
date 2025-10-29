#!/bin/bash

# Configuration - modify these variables as needed
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="spotify"
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_SCHEMA="public"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print with color
echo_color() {
    echo -e "${GREEN}$1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}$1${NC}"
}

echo_error() {
    echo -e "${RED}$1${NC}"
}

# Function to check if PostgreSQL is running and accessible
check_postgres() {
    echo_color "Checking PostgreSQL connection..."
    if ! pg_isready -h $DB_HOST -p $DB_PORT &> /dev/null; then
        echo_error "PostgreSQL is not running or not accessible at $DB_HOST:$DB_PORT"
        echo_warning "Please run ./setup_postgres.sh to set up PostgreSQL"
        return 1
    fi
    
    # Try to connect to the database
    if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" &> /dev/null; then
        echo_error "Cannot connect to PostgreSQL database $DB_NAME with user $DB_USER"
        echo_warning "Please run ./setup_postgres.sh to set up PostgreSQL"
        return 1
    fi
    
    echo_color "PostgreSQL connection successful!"
    return 0
}

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo_error "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check PostgreSQL connection
check_postgres || exit 1

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo_color "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo_color "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo_color "Installing required packages..."
pip install -r requirements.txt

# Add src to PYTHONPATH
echo_color "Setting up PYTHONPATH..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Function to extract credentials from app_config.ini
extract_credentials() {
    local config_file=$1
    if [ -f "$config_file" ]; then
        echo_color "Found config file at $config_file, checking for Spotify credentials..."
        
        # Check if the file has INI format with sections
        if grep -q "\[spotify\]" "$config_file"; then
            echo_color "File has INI format with sections, using section-based extraction"
            
            # Extract from [spotify] section
            SPOTIFY_CLIENT_ID=$(grep -A 10 "\[spotify\]" "$config_file" | grep "spotify_consumer_key" | cut -d '=' -f2 | tr -d ' ')
            if [ ! -z "$SPOTIFY_CLIENT_ID" ]; then
                echo_color "Found spotify_consumer_key in $config_file"
            fi
            
            SPOTIFY_CLIENT_SECRET=$(grep -A 10 "\[spotify\]" "$config_file" | grep "spotify_secret_key" | cut -d '=' -f2 | tr -d ' ')
            if [ ! -z "$SPOTIFY_CLIENT_SECRET" ]; then
                echo_color "Found spotify_secret_key in $config_file"
            fi
            
            SPOTIFY_REDIRECT_URI=$(grep -A 10 "\[spotify\]" "$config_file" | grep "spotify_redirect_uri" | cut -d '=' -f2 | tr -d ' ')
            if [ ! -z "$SPOTIFY_REDIRECT_URI" ]; then
                echo_color "Found spotify_redirect_uri in $config_file"
            else
                SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
            fi
        else
            # Try standard naming convention
            if grep -q "SPOTIFY_CLIENT_ID" "$config_file"; then
                SPOTIFY_CLIENT_ID=$(grep "SPOTIFY_CLIENT_ID" "$config_file" | cut -d '=' -f2 | tr -d ' ')
                echo_color "Found SPOTIFY_CLIENT_ID in $config_file"
            fi
            
            # Try alternative naming convention
            if [ -z "$SPOTIFY_CLIENT_ID" ] && grep -q "spotify_consumer_key" "$config_file"; then
                SPOTIFY_CLIENT_ID=$(grep "spotify_consumer_key" "$config_file" | cut -d '=' -f2 | tr -d ' ')
                echo_color "Found spotify_consumer_key in $config_file"
            fi
            
            # Try standard naming convention
            if grep -q "SPOTIFY_CLIENT_SECRET" "$config_file"; then
                SPOTIFY_CLIENT_SECRET=$(grep "SPOTIFY_CLIENT_SECRET" "$config_file" | cut -d '=' -f2 | tr -d ' ')
                echo_color "Found SPOTIFY_CLIENT_SECRET in $config_file"
            fi
            
            # Try alternative naming convention
            if [ -z "$SPOTIFY_CLIENT_SECRET" ] && grep -q "spotify_secret_key" "$config_file"; then
                SPOTIFY_CLIENT_SECRET=$(grep "spotify_secret_key" "$config_file" | cut -d '=' -f2 | tr -d ' ')
                echo_color "Found spotify_secret_key in $config_file"
            fi
            
            # Try standard naming convention
            if grep -q "SPOTIFY_REDIRECT_URI" "$config_file"; then
                SPOTIFY_REDIRECT_URI=$(grep "SPOTIFY_REDIRECT_URI" "$config_file" | cut -d '=' -f2 | tr -d ' ')
                echo_color "Found SPOTIFY_REDIRECT_URI in $config_file"
            fi
            
            # Try alternative naming convention
            if [ -z "$SPOTIFY_REDIRECT_URI" ] && grep -q "spotify_redirect_uri" "$config_file"; then
                SPOTIFY_REDIRECT_URI=$(grep "spotify_redirect_uri" "$config_file" | cut -d '=' -f2 | tr -d ' ')
                echo_color "Found spotify_redirect_uri in $config_file"
            else
                SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
            fi
        fi
        
        # Debug output
        if [ -z "$SPOTIFY_CLIENT_ID" ] || [ -z "$SPOTIFY_CLIENT_SECRET" ]; then
            echo_warning "Could not find Spotify credentials in $config_file"
            echo_warning "File contents:"
            cat "$config_file"
            return 1
        else
            return 0
        fi
    else
        return 1
    fi
}

# Check for Spotify credentials in app_config.ini in various locations
CONFIG_LOCATIONS=(
    "app_config.ini"                  # Project root
    "src/app_config.ini"              # src directory
    "src/spotify/app_config.ini"      # src/spotify directory
    "src/spotify/config/app_config.ini" # src/spotify/config directory
    "src/app_config/app_config.ini"   # src/app_config directory
)

CREDENTIALS_FOUND=false
for config_file in "${CONFIG_LOCATIONS[@]}"; do
    if extract_credentials "$config_file"; then
        CREDENTIALS_FOUND=true
        break
    fi
done

# Check if Spotify credentials are set
if [ -z "$SPOTIFY_CLIENT_ID" ] || [ -z "$SPOTIFY_CLIENT_SECRET" ]; then
    echo_warning "Warning: Spotify credentials not found in environment or config files"
    echo "Please set your Spotify credentials:"
    read -p "Enter your Spotify Client ID: " client_id
    read -p "Enter your Spotify Client Secret: " client_secret
    export SPOTIFY_CLIENT_ID=$client_id
    export SPOTIFY_CLIENT_SECRET=$client_secret
    export SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
    
    # Ask if user wants to save credentials to app_config.ini
    read -p "Do you want to save these credentials to app_config.ini? (y/n): " save_credentials
    if [[ $save_credentials == "y" || $save_credentials == "Y" ]]; then
        echo "SPOTIFY_CLIENT_ID=$client_id" > app_config.ini
        echo "SPOTIFY_CLIENT_SECRET=$client_secret" >> app_config.ini
        echo "SPOTIFY_REDIRECT_URI=http://localhost:8888/callback" >> app_config.ini
        echo_color "Credentials saved to app_config.ini"
    fi
else
    # Export the variables found in app_config.ini
    export SPOTIFY_CLIENT_ID
    export SPOTIFY_CLIENT_SECRET
    export SPOTIFY_REDIRECT_URI
fi

# Create a wrapper script to run the async code with timeout
echo_color "Creating wrapper script for async execution with timeout..."
cat > run_async_export.py << 'EOF'
import asyncio
import sys
import os
import signal
import time
import logging
from src.spotify.spotify_postgres_saver import save_spotify_data_to_postgres

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global flag to track if the operation timed out
timed_out = False

def timeout_handler(signum, frame):
    global timed_out
    timed_out = True
    logger.error("Operation timed out after 300 seconds (5 minutes)")
    logger.error("The script may be hanging. Please check the logs for more information.")

async def main():
    # Get command line arguments
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_port = int(os.environ.get('DB_PORT', 5432))
    db_name = os.environ.get('DB_NAME', 'spotify')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'postgres')
    schema = os.environ.get('DB_SCHEMA', 'public')
    pickle_first = os.environ.get('NO_PICKLE', 'false').lower() != 'true'
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300)  # 5 minutes timeout
    
    try:
        logger.info("Starting Spotify data export to PostgreSQL...")
        logger.info(f"Connecting to database: {db_host}:{db_port}/{db_name} as {db_user}")
        
        # Run the async function
        await save_spotify_data_to_postgres(
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            schema=schema,
            pickle_first=pickle_first,
        )
        
        # Disable the alarm
        signal.alarm(0)
        
        if timed_out:
            logger.error("Operation completed after timeout. This may indicate a problem.")
        else:
            logger.info("Operation completed successfully.")
    except Exception as e:
        logger.error(f"Error during export: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
EOF

# Set environment variables for the wrapper script
export DB_HOST="$DB_HOST"
export DB_PORT="$DB_PORT"
export DB_NAME="$DB_NAME"
export DB_USER="$DB_USER"
export DB_PASSWORD="$DB_PASSWORD"
export DB_SCHEMA="$DB_SCHEMA"
export NO_PICKLE="false"

# Run the wrapper script
echo_color "Running Spotify PostgreSQL export..."
echo_color "This may take a while. The script will timeout after 5 minutes if it appears to be hanging."
python run_async_export.py

# Check if the script timed out
if [ $? -eq 1 ]; then
    echo_error "Export failed. Please check the logs for more information."
    echo_warning "If the script is hanging, try running with a different database user or check your PostgreSQL configuration."
fi

# Clean up
rm run_async_export.py

# Deactivate virtual environment
deactivate

echo_color "Export process completed!" 