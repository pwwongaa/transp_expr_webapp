#!/usr/bin/env bash
set -e  # exit immediately if any command fails

# 1. Start the frontend dev server in your base environment
echo "Starting frontend in client/..."
(
  cd client
  npm run dev
) &  # run in background

# 2. Activate Conda environment for your backend
echo "Activating Conda environment 'ucl_webapp'..."
source activate ucl_webapp

# 3. Start the backend with Uvicorn
echo "Starting FastAPI backend in server/..."
(
  cd server
  uvicorn main:app --reload
)

# 4. Wait for background jobs (frontend) to exit if you ever stop the script
wait
