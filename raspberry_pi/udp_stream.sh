#!/bin/bash

# Raspberry Pi UDP Video Streaming Script using rpicam-vid
#
# This script uses the native rpicam-vid command to stream video directly 
# over UDP to a specified IP address and port.
#
# This is intended for low-latency direct streaming and does not interact 
# with the Roast Bot FastAPI backend.
#
# Requirements:
# - libcamera-apps (provides rpicam-vid) installed on the Raspberry Pi
# - A .env file in the same directory with UDP_STREAM_TARGET_IP and UDP_STREAM_TARGET_PORT

# Function to load .env file variables
load_env() {
  local env_file=".env"
  if [ -f "$env_file" ]; then
    echo "Loading environment variables from $env_file"
    # Use grep to extract variable assignments, remove comments/empty lines, and export them
    export $(grep -v '^#' "$env_file" | grep -v '^$' | xargs)
  else
    echo "Warning: .env file not found in the current directory."
  fi
}

# Load environment variables
load_env

# Check if required variables are set
if [ -z "${UDP_STREAM_TARGET_IP}" ] || [ -z "${UDP_STREAM_TARGET_PORT}" ]; then
  echo "Error: UDP_STREAM_TARGET_IP and UDP_STREAM_TARGET_PORT must be set in the .env file."
  exit 1
fi

# Construct the rpicam-vid command
# -t 0: Run indefinitely until stopped
# -n: No preview window
# --inline: Include SPS/PPS headers inline for easier decoding
# -o udp://<ip>:<port>: Output via UDP
RPICAM_COMMAND=("rpicam-vid" "-t" "0" "-n" "--inline" "-o" "udp://${UDP_STREAM_TARGET_IP}:${UDP_STREAM_TARGET_PORT}")

# Add any additional user-defined options from RPICAM_VIDEO_OPTIONS
if [ -n "${RPICAM_VIDEO_OPTIONS}" ]; then
  # Split the options string into an array and append
  read -ra EXTRA_OPTIONS <<< "${RPICAM_VIDEO_OPTIONS}"
  RPICAM_COMMAND+=("${EXTRA_OPTIONS[@]}")
fi

# Function to handle script termination
cleanup() {
  echo "\nStopping rpicam-vid..."
  # Check if the process exists before trying to kill it
  if kill -0 $RPICAM_PID 2>/dev/null; then
    kill $RPICAM_PID
  fi
  exit 0
}

# Trap signals to ensure cleanup
trap cleanup SIGINT SIGTERM

# Check if rpicam-vid exists
if ! command -v rpicam-vid &> /dev/null; then
    echo "Error: 'rpicam-vid' command not found."
    echo "Ensure libcamera-apps is installed on your Raspberry Pi (sudo apt install libcamera-apps)."
    exit 1
fi

# Run the command
echo "Starting UDP stream to ${UDP_STREAM_TARGET_IP}:${UDP_STREAM_TARGET_PORT}..."
echo "Running command: ${RPICAM_COMMAND[@]}"
echo "Press Ctrl+C to stop."

# Execute the command in the background and store its PID
"${RPICAM_COMMAND[@]}" & 
RPICAM_PID=$!

# Wait for the background process to finish (it won't unless interrupted)
wait $RPICAM_PID 