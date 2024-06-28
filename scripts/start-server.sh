#!/bin/bash

#
# Render the config file from environment variables.
#
exit_code=$?
if [ $exit_code != 0 ]; then
  echo "Error ${exit_code} encountered rendering the service configuration, NOT STARTING SERVER"
  exit 1
fi

#
# Run initialization script.
# This script will carry out various tasks to ensure a good environment.
# E.g. check database connection, check database version, carry out any
# upgrades if necessary, ensure indexes are in place, etc.
#
scripts/service-initialization.sh
exit_code=$?
if [ $exit_code != 0 ]; then
  echo "Error ${exit_code} encountered during service initialization, NOT STARTING SERVER"
  exit 1
fi

#
# Start the server
#
echo "Running in PROD mode; server will NOT reload when source changes"
poetry run uvicorn orcidlink.main:app --host 0.0.0.0 --port 5000 --log-config=log_config.yaml
