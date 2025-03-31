import io
import os
import requests
import time
from picamera2 import Picamera2

# === CONFIGURATION ===
SERVER_IP = "192.168.86.137"  # Replace with your actual server IP
SERVER_PORT = "8000"         # Replace if your server uses a different port
STREAM_URL = f"http://{SERVER_IP}:{SERVER_PORT}/api/raspi/upload_frame"

print(f"Streaming video to {STREAM_URL}")

# Initialize the camera
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

# Give the camera time to warm up
print("Warming up camera...")
time.sleep(2)

# Use a BytesIO stream to hold the image data
stream = io.BytesIO()

try:
    print("Starting video stream. Press Ctrl+C to stop.")

    while True:
        stream.seek(0)
        stream.truncate()

        # Capture image to stream
        picam2.capture_file(stream, format='jpeg')

        # Reset stream position
        stream.seek(0)

        try:
            response = requests.post(
                STREAM_URL,
                files={'frame': ('image.jpg', stream.read(), 'image/jpeg')},
                data={'stream_id': 'picamera'},
                timeout=1.0
            )

            if response.status_code == 200:
                print(".", end="", flush=True)
            else:
                print(f"\nError: Server returned status code {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"\nRequest error: {e}")
            time.sleep(1)

        time.sleep(0.1)  # Small delay to reduce network load

except KeyboardInterrupt:
    print("\nStopping video stream...")

finally:
    picam2.close()
    print("Camera released. Stream ended.")

