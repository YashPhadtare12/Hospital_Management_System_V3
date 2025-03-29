#!/usr/bin/env bash
set -o errexit

# Create database directory if it doesn't exist
mkdir -p /var/lib/sqlite

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from database import init_db; init_db()"
