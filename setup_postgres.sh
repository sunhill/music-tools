#!/bin/bash

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

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo_error "PostgreSQL is not installed. Please install PostgreSQL and try again."
    echo_warning "On macOS, you can install it with: brew install postgresql"
    echo_warning "On Ubuntu/Debian, you can install it with: sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

# Check if PostgreSQL service is running
if ! pg_isready &> /dev/null; then
    echo_warning "PostgreSQL service is not running. Attempting to start it..."
    
    # Try to start PostgreSQL service
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services start postgresql
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo service postgresql start
    else
        echo_error "Unsupported operating system. Please start PostgreSQL service manually."
        exit 1
    fi
    
    # Wait for PostgreSQL to start
    sleep 3
    
    # Check if PostgreSQL is now running
    if ! pg_isready &> /dev/null; then
        echo_error "Failed to start PostgreSQL service. Please start it manually and try again."
        exit 1
    fi
fi

echo_color "PostgreSQL service is running."

# Create the postgres user if it doesn't exist
echo_color "Creating postgres user if it doesn't exist..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    createuser -s postgres || echo_warning "User postgres already exists or creation failed."
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo -u postgres createuser -s postgres || echo_warning "User postgres already exists or creation failed."
else
    echo_warning "Unsupported operating system. Please create the postgres user manually."
fi

# Create the spotify database if it doesn't exist
echo_color "Creating spotify database if it doesn't exist..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    createdb -U postgres spotify || echo_warning "Database spotify already exists or creation failed."
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo -u postgres createdb spotify || echo_warning "Database spotify already exists or creation failed."
else
    echo_warning "Unsupported operating system. Please create the spotify database manually."
fi

# Set password for postgres user
echo_color "Setting password for postgres user..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD 'postgres';" || echo_warning "Failed to set password for postgres user."
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';" || echo_warning "Failed to set password for postgres user."
else
    echo_warning "Unsupported operating system. Please set the password for postgres user manually."
fi

echo_color "PostgreSQL setup complete!"
echo_color "You can now run the Spotify export script with: ./run_postgres_export.sh" 