import io
import os
import requests
import time
from picamera import PiCamera
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get server IP and port from environment variables
SERVER_IP = os.getenv("IP")
SERVER_PORT = os.getenv("PORT", "8000")  # Default to 8000 if not specified

# Check if environment variables are set
if not SERVER_IP:
    print("Error: IP address not set in .env file")
    exit(1)

# Construct the endpoint URL
STREAM_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api/raspi/upload_frame"

print(f"Streaming video to {STREAM_URL}")

# Initialize the camera
camera = PiCamera()
camera.resolution = (640, 480)  # Adjust as needed
camera.framerate = 10           # Keep framerate low for network efficiency

# Camera warm-up time
print("Warming up camera...")
time.sleep(2)

# Create a stream for capturing images
stream = io.BytesIO()

try:
    print("Starting video stream. Press Ctrl+C to stop.")
    
    # Continuous capture loop
    for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        # Prepare the stream for reading
        stream.seek(0)
        
        # Define a simple unique ID for this stream/camera
        stream_id = "picamera"
        
        try:
            # Send the frame to the server
            response = requests.post(
                STREAM_URL,
                files={
                    'frame': ('image.jpg', stream.read(), 'image/jpeg')
                },
                data={
                    'stream_id': stream_id
                },
                timeout=1.0  # Set a timeout to avoid hanging
            )
            
            if response.status_code == 200:
                print(".", end="", flush=True)  # Simple progress indicator
            else:
                print(f"Error: Server returned status code {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"\nRequest error: {e}")
            time.sleep(1)  # Wait a bit before retrying
            
        # Reset the stream for the next frame
        stream.seek(0)
        stream.truncate()
        
        # Small delay to control frame rate
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\nStopping video stream...")
    
finally:
    # Clean up resources
    camera.close()
    print("Camera released. Stream ended.")
