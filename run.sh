#!/bin/bash

# Function to handle script termination
cleanup() {
    echo "Shutting down servers..."
    kill $(jobs -p) 2>/dev/null
    exit
}

# Set up trap for cleanup on script termination
trap cleanup SIGINT SIGTERM

# Start Python backend
echo "Starting Python backend..."
cd server/python
# Add the current directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 run.py &
BACKEND_PID=$!

# Wait a moment for the backend to start
sleep 2

# Start frontend development server
echo "Starting frontend development server..."
cd ../..  # Go back to root directory
npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 