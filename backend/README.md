# Roast Bot Backend

This is the backend server for Roast Bot, a system that generates funny roasts using Perplexity AI and ElevenLabs text-to-speech, and supports video streaming from Raspberry Pi clients.

## Setup

1. Create a virtual environment:
   ```
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables in `backend/.env`:
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

## Raspberry Pi Integration (Moved to `/raspberry_pi` directory)

Roast Bot includes support for Raspberry Pi hardware integration for both audio roasts and video streaming. The client scripts and their dependencies are now located in the separate `/raspberry_pi` directory in the project root.

Please refer to the `README.md` within the `/raspberry_pi` directory for specific setup instructions and usage details for the Raspberry Pi clients.

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

### Raspberry Pi Integration Endpoints (Backend)

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
