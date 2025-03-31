# Raspberry Pi Clients for Roast Bot

This directory contains the client scripts designed to run on a Raspberry Pi for interacting with the Roast Bot backend.

## Scripts

- `raspi_client.py`: Triggers a roast request to the backend, receives the audio, and plays it using `pygame`.
- `raspi_stream.py`: Captures video from a connected camera using `opencv-python` and streams it to the backend.

## Setup

1.  **Install Dependencies**:

    ```bash
    # Navigate to this directory
    cd raspberry_pi 
    
    # Create a virtual environment (optional but recommended)
    python -m venv .venv
    source .venv/bin/activate
    
    # Install required packages
    pip install -r requirements.txt
    ```

2.  **Create `.env` File**:
    Create a file named `.env` in this `raspberry_pi` directory and add the following configuration:

    ```dotenv
    # URL of your running Roast Bot backend server
    API_URL=http://<your_server_ip_or_hostname>:8000 
    
    # The API key configured in the backend's .env file (RASPI_API_KEY)
    RASPI_API_KEY=your_custom_api_key_for_raspberry_pi
    
    # --- Settings for raspi_client.py (Audio Roasts) ---
    # Default User ID to associate the roast request with (get this from the web UI or API)
    USER_ID=target_user_uuid 
    
    # --- Settings for raspi_stream.py (Video Streaming) ---
    # A unique name for this camera stream (e.g., "living_room_cam", "front_door")
    STREAM_ID=your_camera_name 
    ```

    Replace `<your_server_ip_or_hostname>` with the actual IP address or hostname where your backend server is running.

## Usage

### Audio Roast Client (`raspi_client.py`)

This script sends a request to generate a roast for a specific name and plays the resulting audio.

```bash
python raspi_client.py "Person To Roast"
```

**Options:**

-   `name` (Positional Argument): The name of the person to roast. Defaults to "Guest" if not provided.
-   `--voice` or `-v`: The voice ID or predefined name (e.g., `male1`, `villain`, `female2`) to use for the text-to-speech generation. Defaults to `villain`.
-   `--list-voices` or `-l`: Lists the available predefined voice names and their IDs.

**Example:**

```bash
# Roast "Alice" using the "female1" voice
python raspi_client.py "Alice" --voice female1

# List available voices
python raspi_client.py --list-voices
```

*Note: Ensure you have a speaker or audio output configured on your Raspberry Pi.* Requires `pygame` library.

### Video Streaming Client (`raspi_stream.py`)

This script continuously captures video from the default camera (usually `/dev/video0`) and sends the frames to the backend server for processing and viewing.

```bash
python raspi_stream.py
```

Press `Ctrl+C` to stop the stream.

*Note: Requires `opencv-python` and `numpy` libraries. Make sure your camera is properly connected and configured on the Raspberry Pi.* 