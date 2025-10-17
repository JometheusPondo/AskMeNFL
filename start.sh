#!/bin/bash

# Check if database exists
if [ ! -f "/app/nfl_complete_database.db" ]; then
    echo "First run - downloading NFL database"
    python nfl-db-downloader.py <<EOF
yes
EOF
    echo "Database download complete!"
else
    echo "Database found, skipping download"
fi

# Create users database if needed
if [ ! -f "/app/nfl_users.db" ]; then
    touch /app/nfl_users.db
fi

# Start server
uvicorn main:app --host 0.0.0.0 --port 8000