#!/bin/bash
# Script to run the Python Flask backend with LangChain

echo "Starting Python backend with Flask and LangChain..."

# Add the project root to PYTHONPATH for proper imports
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run the Python backend
cd server/python
python3 run.py