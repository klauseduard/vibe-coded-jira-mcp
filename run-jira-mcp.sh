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

# Install dependencies with --break-system-packages flag (note: this is a temporary solution)
echo "Installing dependencies..." >&2
python3 -m pip install --break-system-packages -r "$(dirname "$0")/requirements.txt" >&2

# Run the script
exec /usr/bin/python3 "$(dirname "$0")/simple_jira.py" "$@" 