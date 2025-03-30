#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Only initialize database if it's a fresh deployment
if [ "$RENDER" ]; then
  python database.py
fi
