# Roast Bot Backend

This is the backend server for Roast Bot, a system that generates funny roasts using Perplexity AI and ElevenLabs text-to-speech.

## Setup

1. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables in `.env`:
   ```
   SECRET_KEY=your_secret_key
   PERPLEXITY_API_KEY=your_perplexity_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   RASPI_API_KEY=your_custom_api_key_for_raspberry_pi
   ```

4. Run the server:
   ```
   python -m main
   ```

## Raspberry Pi Integration

### Audio Roast Integration

Roast Bot includes support for Raspberry Pi hardware integration, allowing physical devices to trigger roasts with spoken audio output.

#### How It Works

1. The Raspberry Pi sends a request to the backend API with a user ID and name.
2. The backend generates a roast based on the characteristics configured for that user.
3. The roast is converted to speech using ElevenLabs API.
4. The audio is returned to the Raspberry Pi which can play it through connected speakers.

#### Setup Instructions for Audio Roast

1. Install required dependencies on your Raspberry Pi:
   ```
   pip install requests python-dotenv pygame
   ```

2. Create a `.env` file on your Raspberry Pi with the following:
   ```
   API_URL=http://your-server-url:8000
   RASPI_API_KEY=your_custom_api_key_for_raspberry_pi
   USER_ID=target_user_uuid
   ```

3. Copy the `raspi_client.py` script to your Raspberry Pi.

4. Run the script to trigger a roast:
   ```
   python raspi_client.py "Person's Name"
   ```

#### Audio Command Line Options

The `raspi_client.py` script supports the following options:

- `name`: The name of the person to roast (first positional argument)
- `--voice` or `-v`: Voice to use for TTS (default: "villain")
- `--list-voices` or `-l`: List available voice options

Example:
```
python raspi_client.py "John Doe" --voice female1
```

### Video Streaming Integration

Roast Bot now supports video streaming from a Raspberry Pi camera, with future support for facial recognition and analysis using DeepFace.

#### How It Works

1. The Raspberry Pi captures video frames from a connected camera
2. Frames are compressed and sent to the backend server
3. The server processes frames with analysis (placeholder for DeepFace)
4. Video streams can be viewed in a web browser

#### Setup Instructions for Video Streaming

1. Install required dependencies on your Raspberry Pi:
   ```
   pip install requests python-dotenv opencv-python numpy
   ```

2. Create a `.env` file on your Raspberry Pi with the following:
   ```
   API_URL=http://your-server-url:8000
   RASPI_API_KEY=your_custom_api_key_for_raspberry_pi
   STREAM_ID=your_camera_name  # e.g., "living_room", "entrance", etc.
   ```

3. Copy the `raspi_stream.py` script to your Raspberry Pi.

4. Run the script to start streaming:
   ```
   python raspi_stream.py
   ```

5. To view the stream in a web browser, navigate to:
   ```
   http://your-server-url:8000/viewer
   ```

#### Viewing Streams

You can access the stream viewer web interface at `/viewer`. This page allows you to:
- See all active streams
- Select a stream to view
- See analysis results from each frame (will be enhanced with DeepFace in the future)

## API Endpoints

### Authentication

- `POST /auth/register`: Register a new user
- `POST /auth/login`: Login and get access token

### Users

- `GET /users/me`: Get current user's profile
- `PUT /users/me`: Update current user's profile
- `POST /users/me/profile-image`: Upload a profile image
- `GET /users`: Get all users

### Roasts

- `PUT /users/{target_user_id}/roast-config`: Update roast configuration for a user
- `GET /users/{target_user_id}/roast-config`: Get roast configuration for a user
- `POST /users/{target_user_id}/roast`: Roast a user
- `GET /users/{target_user_id}/all-roasts`: Get all roasts for a user
- `POST /api/generate-roast/{user_id}`: Generate a roast for a user
- `GET /api/roast-history/{user_id}`: Get roast history for a user

### Raspberry Pi Integration

- `POST /api/raspi/trigger-roast`: Generate a roast and return as audio (requires API key)
- `POST /api/raspi/stream-frame`: Send a video frame from the Raspberry Pi (requires API key)
- `GET /api/streams`: Get list of active video streams (requires authentication)
- `GET /api/stream/{stream_id}`: Get analysis data for a stream (requires authentication)
- `GET /api/stream/{stream_id}/video`: Get video stream (requires authentication)
- `GET /api/public-stream/{stream_id}/{api_key}`: Get public video stream (requires API key in URL)

### Web Interface

- `GET /viewer`: HTML page for viewing video streams

## Development

The backend is built with FastAPI and SQLite for data storage. It integrates with:
- Perplexity AI for generating roasts
- ElevenLabs for text-to-speech conversion
- DeepFace for facial analysis (coming soon)
