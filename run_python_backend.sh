#!/bin/bash
# Script to run the Python Flask backend with LangChain

echo "Starting Python backend with Flask and LangChain..."

# Add the project root to PYTHONPATH for proper imports
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Configure Python backend to run on port 5001
export PORT=5001

# Run the Python backend
cd server/python
python3 run.py