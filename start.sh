#!/bin/bash
# Airport Navigation Assistant - Start Script

set -e
cd "$(dirname "$0")"  # always run from project root

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
fi

# Set Google credentials if .env exists
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting server at http://localhost:8000"
echo "Simulation: http://localhost:8000/simulation.html"
echo ""

# Open browser after a short delay (background)
(sleep 1.5 && open "http://localhost:8000/simulation.html") &

# Start FastAPI (foreground, so Ctrl+C stops it cleanly)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
