#!/bin/bash

mkdir -p /app/data

# Check if database exists
if [ ! -f "/app/nfl_complete_database.db" ]; then
    echo "First run - downloading NFL database"
    cd /app/data
    python /app/nfl-db-downloader.py /app/data/nfl_complete_database.db <<EOF
yes
EOF
    echo "Database download complete!"
else
    echo "Database found, skipping download"
fi

# Create users database if needed
if [ ! -f "/app/data/nfl_users.db" ]; then
    touch /app/data/nfl_users.db
fi

# Start server
cd /app
uvicorn main:app --host 0.0.0.0 --port 8000