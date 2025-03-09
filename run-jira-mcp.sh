#!/bin/bash
# Reset problematic environment variables
unset PYTHONHOME
unset PYTHONPATH

# Create logs directory
mkdir -p "$(dirname "$0")/logs"

# Log environment for debugging
echo "Running with clean environment" >&2
echo "PATH: $PATH" >&2
echo "PWD: $PWD" >&2

# Run the script
exec /usr/bin/python3 "$(dirname "$0")/simple_jira.py" "$@" 