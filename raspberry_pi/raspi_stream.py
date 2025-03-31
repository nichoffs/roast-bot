#!/usr/bin/env python3
"""
Raspberry Pi Video Streaming Client

This script captures video from a Raspberry Pi camera and streams it to the backend server.
The backend will process the frames (e.g., with deepface analysis in the future).

Requirements:
- opencv-python
- requests
- python-dotenv
- numpy
"""

import os
import cv2
import time
import base64
import requests
import numpy as np
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("RASPI_API_KEY", "raspberry_secret_key")
STREAM_ID = os.getenv("STREAM_ID", "camera1")  # Unique identifier for this camera
FPS = 10  # Target frames per second
JPEG_QUALITY = 70  # Lower for faster transmission (0-100)

class VideoStreamClient:
    def __init__(self, camera_id=0, resolution=(640, 480)):
        """
        Initialize the video streaming client
        
        Args:
            camera_id: Camera device ID (usually 0 for the first camera)
            resolution: Video resolution (width, height)
        """
        self.camera_id = camera_id
        self.resolution = resolution
        self.is_running = False
        self.cap = None
        self.thread = None
    
    def start(self):
        """Start the video streaming thread"""
        self.is_running = True
        self.cap = cv2.VideoCapture(self.camera_id)
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        
        if not self.cap.isOpened():
            raise Exception(f"Could not open camera {self.camera_id}")
        
        # Start the streaming thread
        self.thread = Thread(target=self._stream_frames)
        self.thread.daemon = True
        self.thread.start()
        
        print(f"Started streaming from camera {self.camera_id}")
    
    def stop(self):
        """Stop the video streaming thread"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.cap:
            self.cap.release()
        print("Stopped streaming")
    
    def _stream_frames(self):
        """Main streaming function that runs in a thread"""
        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        
        # Calculate the delay between frames to maintain the target FPS
        frame_delay = 1.0 / FPS
        
        while self.is_running:
            loop_start = time.time()
            
            # Capture frame
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to capture frame")
                time.sleep(0.1)
                continue
            
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            
            # Convert to base64 for transmission
            encoded_frame = base64.b64encode(buffer).decode('utf-8')
            
            # Send frame to server
            payload = {
                "stream_id": STREAM_ID,
                "frame": encoded_frame,
                "timestamp": time.time()
            }
            
            try:
                # Non-blocking request
                thread = Thread(target=self._send_frame, args=(headers, payload))
                thread.daemon = True
                thread.start()
                
                # Calculate time to sleep to maintain FPS
                processing_time = time.time() - loop_start
                sleep_time = max(0, frame_delay - processing_time)
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error sending frame: {e}")
                time.sleep(0.1)
    
    def _send_frame(self, headers, payload):
        """Send a single frame to the server"""
        try:
            response = requests.post(
                f"{API_URL}/api/raspi/stream-frame", 
                headers=headers,
                json=payload,
                timeout=0.5  # Short timeout to avoid blocking
            )
            
            if response.status_code != 200:
                print(f"Server error: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

def main():
    """Main function"""
    print("Starting Raspberry Pi video streaming client")
    
    # Create and start the streaming client
    client = VideoStreamClient(camera_id=0, resolution=(640, 480))
    
    try:
        client.start()
        print("Streaming video to server. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        client.stop()

if __name__ == "__main__":
    main() 