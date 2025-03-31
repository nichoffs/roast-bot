# Raspberry Pi Camera Integration for Roast Bot

This directory contains the client script designed to run on a Raspberry Pi for sending camera frames to the Roast Bot backend for DeepFace analysis.

## Script

- `send_video.py`: Uses the Raspberry Pi Camera (`picamera` library) to stream video frames directly to the backend server's API for DeepFace analysis.

## Setup

1.  **Install Dependencies**:

    ```bash
    # Navigate to this directory
    cd raspberry_pi 
    
    # Create a virtual environment (optional but recommended)
    python -m venv .venv
    source .venv/bin/activate
    
    # Install required Python packages
    pip install -r requirements.txt
    
    # For PiCamera usage (send_video.py)
    # Make sure the camera is enabled in raspi-config:
    sudo raspi-config  # Navigate to Interfacing Options > Camera > Enable
    ```

2.  **Create `.env` File**:
    Create a file named `.env` in this `raspberry_pi` directory and add the following configuration:

    ```dotenv
    # Server connection settings
    IP=<your_server_ip_address>  # Change this to your server's IP address
    PORT=8000  # Default port for the backend
    ```

    Replace `<your_server_ip_address>` with the actual IP address of your Roast Bot backend server.

## Usage

### PiCamera Video Streaming (`send_video.py`)

This script uses the Raspberry Pi's dedicated camera module to capture video frames and send them directly to the backend server's API for DeepFace analysis.

```bash
python send_video.py
```

Press `Ctrl+C` to stop the stream.

Features:
- Uses the official `picamera` library for optimal performance on Raspberry Pi
- Sends JPEG frames directly to the backend's API endpoint
- Automatically handles reconnection if the server connection is lost
- Shows a simple progress indicator while streaming

*Note: Requires the Raspberry Pi Camera Module to be connected and enabled.* 