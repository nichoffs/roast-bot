mport io
import requests
import time
from picamera import PiCamera

camera = PiCamera()
camera.resolution = (640, 480)  # Adjust as needed
camera.framerate = 10           # Keep framerate low for Pi Zero

time.sleep(2)  # Camera warm-up time

stream = io.BytesIO()

for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        stream.seek(0)
            requests.post('http://192.168.86.137:8000/upload_frame', files={'frame': stream.read()})
                stream.seek(0)
                    stream.truncate()
