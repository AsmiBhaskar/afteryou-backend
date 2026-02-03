#!/bin/bash
# Start Celery worker and beat scheduler for development

echo "Starting Celery worker and beat scheduler..."

# Start Celery worker in background
celery -A afteryou worker --loglevel=info &
WORKER_PID=$!

# Start Celery beat scheduler in background  
celery -A afteryou beat --loglevel=info &
BEAT_PID=$!

echo "Celery worker PID: $WORKER_PID"
echo "Celery beat PID: $BEAT_PID"

# Function to cleanup processes on exit
cleanup() {
    echo "Stopping Celery processes..."
    kill $WORKER_PID 2>/dev/null
    kill $BEAT_PID 2>/dev/null
    exit
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for processes
wait
