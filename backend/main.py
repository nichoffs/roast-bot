import base64
import io
import json
import os
import sqlite3
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from fastapi import (
    Body,
    Depends,
    FastAPI,
    File,
    Form,
    Header,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import (
    Response,
    StreamingResponse,
)
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from openai import OpenAI
from passlib.context import CryptContext
from PIL import Image
from pydantic import BaseModel, EmailStr, Field

# Load environment variables
load_dotenv()

# Security configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY", "YOUR_SECRET_KEY_HERE"
)  # In production, use a secure key stored in environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Perplexity AI configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# API Key for Raspberry Pi integration - in production, use a more secure randomly generated key
RASPI_API_KEY = os.getenv("RASPI_API_KEY", "raspberry_secret_key")

# ElevenLabs API configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "jsCqWAovK2LkecY7zXl4"  # Default voice ID - could be customized

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize OpenAI client for Perplexity
perplexity_client = OpenAI(
    api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai"
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize FastAPI app
app = FastAPI(title="Roast Bot API")

# Add GZip compression for faster responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create data and uploads directories if they don't exist
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Create templates directory for HTML templates
# TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
# os.makedirs(TEMPLATES_DIR, exist_ok=True)
#
# # Initialize Jinja2 templates
# templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Create static files route for uploads
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

# Database setup
DB_PATH = os.path.join(DATA_DIR, "roastbot.db")

# Base URL for serving static files
BASE_URL = "http://localhost:8000"  # Change this in production

# Create data directories for video streams
STREAMS_DIR = os.path.join(DATA_DIR, "streams")
os.makedirs(STREAMS_DIR, exist_ok=True)

# In-memory storage for active video streams
active_streams = {}
stream_frames = {}
stream_lock = threading.Lock()


# Model for video stream data
class VideoFrame(BaseModel):
    stream_id: str
    frame: str  # Base64 encoded image
    timestamp: float


# DeepFace placeholder function
def deepface_analyze(frame):
    """
    Placeholder for DeepFace analysis
    This will be replaced with actual DeepFace implementation later

    Args:
        frame: Numpy array representing an image

    Returns:
        dict: Analysis results
    """
    # Just a placeholder - implement actual DeepFace integration later
    return {
        "age": 30,
        "emotion": {"happy": 0.8, "neutral": 0.2},
        "gender": "Male",
        "race": {"white": 0.75, "latino": 0.25},
        "timestamp": time.time(),
    }


# Stream frame generator for video streaming endpoint
def stream_frames_generator(stream_id):
    """
    Generator for streaming frames

    Args:
        stream_id: ID of the stream to serve

    Yields:
        bytes: JPEG frame data for streaming
    """
    if stream_id not in stream_frames:
        stream_frames[stream_id] = deque(maxlen=30)  # Store last 30 frames

    # Serve a blank frame if no frames are available
    if len(stream_frames[stream_id]) == 0:
        blank_frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        img = Image.fromarray(blank_frame.astype("uint8"))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.read() + b"\r\n"

    last_frame_time = 0
    min_frame_interval = 1.0 / 15  # Max 15 FPS for streaming

    while True:
        with stream_lock:
            if len(stream_frames[stream_id]) == 0:
                # If no frames available, wait a bit
                time.sleep(0.1)
                continue

            # Get the latest frame
            frame_data = stream_frames[stream_id][-1]

        current_time = time.time()
        if current_time - last_frame_time < min_frame_interval:
            time.sleep(min_frame_interval - (current_time - last_frame_time))

        # Yield the frame in MJPEG format
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_data + b"\r\n"
        last_frame_time = time.time()


def dict_factory(cursor, row):
    """Convert SQL row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    return conn


def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        image TEXT,
        roast_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create index on email for faster login
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    # Create roast_configs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roast_configs (
        user_id TEXT NOT NULL,
        target_user_id TEXT NOT NULL,
        topics TEXT NOT NULL,
        style TEXT NOT NULL,
        PRIMARY KEY (user_id, target_user_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (target_user_id) REFERENCES users(id)
    )
    """)

    # Create indices for faster roast config queries
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_roast_configs_user_id ON roast_configs(user_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_roast_configs_target_user_id ON roast_configs(target_user_id)"
    )

    # Create roast history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roast_history (
        id TEXT PRIMARY KEY,
        target_user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        characteristics TEXT NOT NULL,
        roast_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (target_user_id) REFERENCES users(id)
    )
    """)

    # Create index for roast history
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_roast_history_target_user_id ON roast_history(target_user_id)"
    )

    conn.commit()
    conn.close()


# Initialize database
init_db()


# Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserPublic(BaseModel):
    id: str
    name: str
    image: Optional[str] = None
    roast_count: int = 0


class RoastConfig(BaseModel):
    topics: List[str]
    style: str


class UserRoastConfig(BaseModel):
    user_id: str
    user_name: str
    topics: List[str]
    style: str


class RoastRequest(BaseModel):
    name: str


class RoastHistoryItem(BaseModel):
    id: str
    name: str
    characteristics: List[str]
    roast_text: str
    created_at: str


class TtsFormat(BaseModel):
    format: str = "mp3"  # mp3, pcm, etc.
    voice_id: Optional[str] = None  # Voice ID to use, defaults to system default


# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = get_user_by_id(token_data.user_id)
    if not user:
        raise credentials_exception

    return user


# Routes
@app.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if email already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)

    # Insert user into database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (id, name, email, hashed_password, image, roast_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            user_data.name,
            user_data.email,
            hashed_password,
            "/placeholder.svg?height=100&width=100",  # Default image
            0,
        ),
    )
    conn.commit()
    conn.close()

    return {"id": user_id, "name": user_data.name, "email": user_data.email}


@app.post("/auth/login", response_model=Token)
async def login(user_data: dict = Body(...)):
    email = user_data.get("email")
    password = user_data.get("password")

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email and password are required",
        )

    user = get_user_by_email(email)

    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
    }


@app.get("/users", response_model=List[UserPublic])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    # Return all users except the current user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, image, roast_count
        FROM users
        WHERE id != ?
        """,
        (current_user["id"],),
    )
    all_users = cursor.fetchall()
    conn.close()

    return all_users


@app.put("/users/{target_user_id}/roast-config", response_model=RoastConfig)
async def update_roast_config(
    target_user_id: str,
    config: RoastConfig,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    # Check if target user exists
    target_user = get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update or insert roast config
    conn = get_db_connection()
    cursor = conn.cursor()
    topics_json = json.dumps(config.topics)

    cursor.execute(
        """
        INSERT OR REPLACE INTO roast_configs (user_id, target_user_id, topics, style)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, target_user_id, topics_json, config.style),
    )
    conn.commit()
    conn.close()

    return config


@app.get("/users/{target_user_id}/roast-config", response_model=RoastConfig)
async def get_roast_config(
    target_user_id: str, current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]

    # Check if target user exists
    target_user = get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Get roast config from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT topics, style
        FROM roast_configs
        WHERE user_id = ? AND target_user_id = ?
        """,
        (user_id, target_user_id),
    )
    config = cursor.fetchone()
    conn.close()

    if not config:
        return {"topics": [], "style": "Funny but not too mean"}

    # Parse topics back from JSON
    topics = json.loads(config["topics"])
    return {"topics": topics, "style": config["style"]}


@app.post("/users/{target_user_id}/roast")
async def roast_user(
    target_user_id: str,
    config: RoastConfig,
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    # Check if target user exists
    target_user = get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update roast config
    conn = get_db_connection()
    cursor = conn.cursor()
    topics_json = json.dumps(config.topics)

    cursor.execute(
        """
        INSERT OR REPLACE INTO roast_configs (user_id, target_user_id, topics, style)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, target_user_id, topics_json, config.style),
    )

    # Increment roast count
    cursor.execute(
        """
        UPDATE users
        SET roast_count = roast_count + 1
        WHERE id = ?
        """,
        (target_user_id,),
    )

    cursor.execute("SELECT roast_count FROM users WHERE id = ?", (target_user_id,))
    new_count = cursor.fetchone()["roast_count"]

    conn.commit()
    conn.close()

    return {"success": True, "roast_count": new_count}


@app.get("/users/{target_user_id}/all-roasts", response_model=List[UserRoastConfig])
async def get_all_user_roasts(
    target_user_id: str, current_user: dict = Depends(get_current_user)
):
    # Check if target user exists
    target_user = get_user_by_id(target_user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Get all roast configs for this user from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.user_id, u.name as user_name, r.topics, r.style
        FROM roast_configs r
        JOIN users u ON r.user_id = u.id
        WHERE r.target_user_id = ?
        """,
        (target_user_id,),
    )
    configs = cursor.fetchall()
    conn.close()

    # Format the results
    all_roasts = []
    for config in configs:
        topics = json.loads(config["topics"])
        all_roasts.append(
            {
                "user_id": config["user_id"],
                "user_name": config["user_name"],
                "topics": topics,
                "style": config["style"],
            }
        )

    return all_roasts


@app.post("/users/me/profile-image")
async def update_profile_image(
    image_data: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]

    # Decode base64 image
    try:
        # Remove the data:image/jpeg;base64, part if present
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

        image_bytes = base64.b64decode(image_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image data: {str(e)}",
        )

    # Save image file
    image_filename = f"{user_id}_profile.jpg"
    image_path = os.path.join(UPLOADS_DIR, image_filename)

    with open(image_path, "wb") as f:
        f.write(image_bytes)

    # Update user record with image URL - use absolute URL
    image_rel_path = f"/uploads/{image_filename}"
    image_url = f"{BASE_URL}{image_rel_path}"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users
        SET image = ?
        WHERE id = ?
        """,
        (image_url, user_id),
    )
    conn.commit()
    conn.close()

    return {"image_url": image_url}


@app.put("/users/me", response_model=UserResponse)
async def update_user_profile(
    profile_data: dict = Body(...), current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]

    # Update user fields in database
    conn = get_db_connection()
    cursor = conn.cursor()

    updates = []
    values = []

    if "name" in profile_data:
        updates.append("name = ?")
        values.append(profile_data["name"])

    if "email" in profile_data:
        updates.append("email = ?")
        values.append(profile_data["email"])

    if updates:
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        values.append(user_id)
        cursor.execute(query, values)
        conn.commit()

    # Get updated user data
    cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
    updated_user = cursor.fetchone()
    conn.close()

    return updated_user


@app.post("/api/generate-roast/{user_id}")
async def generate_roast(user_id: str, request: RoastRequest):
    # Check if user exists
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Get all roast configurations for this user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.topics, r.style
        FROM roast_configs r
        WHERE r.target_user_id = ?
        """,
        (user_id,),
    )
    roast_configs = cursor.fetchall()
    conn.close()

    if not roast_configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No roast configurations found for this user",
        )

    # Combine all topics from different roast configs
    all_topics = []
    for config in roast_configs:
        topics = json.loads(config["topics"])
        all_topics.extend(topics)

    # Remove duplicates while preserving order
    characteristics = []
    for topic in all_topics:
        if topic not in characteristics:
            characteristics.append(topic)

    # Limit to 5 characteristics if we have more
    if len(characteristics) > 5:
        characteristics = characteristics[:5]

    # Fill in if we have less than 5
    while len(characteristics) < 5:
        characteristics.append("generic")

    # Create the prompt
    prompt = f"""You are the roast god, a vulgar, vial roaster who can be clever but also blunt and cruel. You're not afraid to be politically incorrect and use all the characteristics and context at your disposal. You will be given a name and a list of characteristics and generate a paragraph long roast about them. There is one key detail: RETURN THE ROAST AND NOTHING BUT THE ROAST. There should be no other text besides this one paragraph roasting whoever it is. Now give it a shot:

NAME: {request.name} 
CHARACTERISTICS:
- {characteristics[0]}
- {characteristics[1]} 
- {characteristics[2]}
- {characteristics[3]}
- {characteristics[4]}"""

    # Call Perplexity API
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a roast bot that generates clever, funny roasts.",
            },
            {"role": "user", "content": prompt},
        ]

        response = perplexity_client.chat.completions.create(
            model="sonar-small-chat",  # Using a smaller model for cost efficiency
            messages=messages,
        )

        roast_text = response.choices[0].message.content

        # Save this roast to history
        roast_id = str(uuid.uuid4())
        characteristics_json = json.dumps(characteristics)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO roast_history (id, target_user_id, name, characteristics, roast_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (roast_id, user_id, request.name, characteristics_json, roast_text),
        )

        # Update the roast count for the user
        cursor.execute(
            """
            UPDATE users
            SET roast_count = roast_count + 1
            WHERE id = ?
            """,
            (user_id,),
        )

        conn.commit()
        conn.close()

        return {"roast": roast_text, "roast_id": roast_id}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating roast: {str(e)}",
        )


@app.get("/api/roast-history/{user_id}", response_model=List[RoastHistoryItem])
async def get_roast_history(
    user_id: str, current_user: dict = Depends(get_current_user)
):
    # Check if user exists
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Get roast history for this user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, characteristics, roast_text, created_at
        FROM roast_history
        WHERE target_user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
        """,
        (user_id,),
    )
    history_items = cursor.fetchall()
    conn.close()

    # Format the response
    formatted_history = []
    for item in history_items:
        characteristics = json.loads(item["characteristics"])
        formatted_history.append(
            {
                "id": item["id"],
                "name": item["name"],
                "characteristics": characteristics,
                "roast_text": item["roast_text"],
                "created_at": item["created_at"],
            }
        )

    return formatted_history


# API Key verification function
async def verify_raspi_api_key(x_api_key: str = Header(None)):
    if x_api_key != RASPI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )
    return x_api_key


@app.post("/api/raspi/trigger-roast")
async def trigger_roast_from_raspi(
    request: dict = Body(...),
    tts_format: Optional[TtsFormat] = None,
    api_key: str = Depends(verify_raspi_api_key),
):
    """
    Endpoint for Raspberry Pi to trigger a roast.
    Expects a JSON body with:
    {
        "user_id": "user-uuid",
        "name": "Person Name",
        "voice_id": "optional-voice-id"  # Optional
    }

    Optional query parameter:
    - format: Audio format (mp3, pcm) - defaults to mp3

    Returns audio data of the roast spoken by ElevenLabs TTS
    """
    user_id = request.get("user_id")
    name = request.get("name")
    voice_id = request.get("voice_id")

    # Set default format and voice
    audio_format = tts_format.format if tts_format else "mp3"
    voice_id = voice_id or tts_format.voice_id if tts_format else ELEVENLABS_VOICE_ID

    if not user_id or not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id and name are required",
        )

    # Check if user exists
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Get all roast configurations for this user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.topics, r.style
        FROM roast_configs r
        WHERE r.target_user_id = ?
        """,
        (user_id,),
    )
    roast_configs = cursor.fetchall()
    conn.close()

    if not roast_configs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No roast configurations found for this user",
        )

    # Combine all topics from different roast configs
    all_topics = []
    for config in roast_configs:
        topics = json.loads(config["topics"])
        all_topics.extend(topics)

    # Remove duplicates while preserving order
    characteristics = []
    for topic in all_topics:
        if topic not in characteristics:
            characteristics.append(topic)

    # Limit to 5 characteristics if we have more
    if len(characteristics) > 5:
        characteristics = characteristics[:5]

    # Fill in if we have less than 5
    while len(characteristics) < 5:
        characteristics.append("generic")

    # Create the prompt
    prompt = f"""You are the roast god, a vulgar, vial roaster who can be clever but also blunt and cruel. You're not afraid to be politically incorrect and use all the characteristics and context at your disposal. You will be given a name and a list of characteristics and generate a paragraph long roast about them. There is one key detail: RETURN THE ROAST AND NOTHING BUT THE ROAST. There should be no other text besides this one paragraph roasting whoever it is. Now give it a shot:

NAME: {name} 
CHARACTERISTICS:
- {characteristics[0]}
- {characteristics[1]} 
- {characteristics[2]}
- {characteristics[3]}
- {characteristics[4]}"""

    # Call Perplexity API to generate the roast
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a roast bot that generates clever, funny roasts.",
            },
            {"role": "user", "content": prompt},
        ]

        response = perplexity_client.chat.completions.create(
            model="sonar-small-chat",  # Using a smaller model for cost efficiency
            messages=messages,
        )

        roast_text = response.choices[0].message.content

        # Save this roast to history
        roast_id = str(uuid.uuid4())
        characteristics_json = json.dumps(characteristics)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO roast_history (id, target_user_id, name, characteristics, roast_text)
            VALUES (?, ?, ?, ?, ?)
            """,
            (roast_id, user_id, name, characteristics_json, roast_text),
        )

        # Update the roast count for the user
        cursor.execute(
            """
            UPDATE users
            SET roast_count = roast_count + 1
            WHERE id = ?
            """,
            (user_id,),
        )

        conn.commit()
        conn.close()

        # Convert text to speech using ElevenLabs
        try:
            output_format = "mp3_44100_128" if audio_format == "mp3" else "pcm_24000"

            audio_data = elevenlabs_client.text_to_speech.convert(
                text=roast_text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format=output_format,
            )

            # Return audio data with appropriate content type
            content_type = "audio/mpeg" if audio_format == "mp3" else "audio/pcm"

            return Response(
                content=audio_data,
                media_type=content_type,
                headers={
                    "Content-Disposition": f"attachment; filename=roast_{roast_id}.{audio_format}"
                },
            )

        except Exception as e:
            # If TTS fails, fall back to returning the text
            print(f"TTS generation failed: {str(e)}")
            return {
                "roast": roast_text,
                "roast_id": roast_id,
                "error": "TTS generation failed, returning text only",
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating roast: {str(e)}",
        )


# API endpoints for video streaming
@app.post("/api/raspi/stream-frame")
async def receive_stream_frame(
    frame_data: VideoFrame, api_key: str = Depends(verify_raspi_api_key)
):
    """
    Endpoint for Raspberry Pi to send video frames

    Args:
        frame_data: VideoFrame model with stream_id, frame data, and timestamp
        api_key: API key for authentication

    Returns:
        dict: Status response
    """
    stream_id = frame_data.stream_id

    # Decode the base64 image
    try:
        img_bytes = base64.b64decode(frame_data.frame)

        # Process with DeepFace (placeholder for now)
        # In a production system, this would be done in a separate worker thread/process
        try:
            # Convert bytes to image for analysis
            img = Image.open(io.BytesIO(img_bytes))
            frame_array = np.array(img)

            # Analyze with DeepFace (placeholder)
            analysis = deepface_analyze(frame_array)

            # Store the active stream information
            with stream_lock:
                active_streams[stream_id] = {
                    "last_frame": time.time(),
                    "analysis": analysis,
                }

                # Add frame to the stream's frame queue
                if stream_id not in stream_frames:
                    stream_frames[stream_id] = deque(maxlen=30)  # Store last 30 frames
                stream_frames[stream_id].append(img_bytes)

        except Exception as e:
            print(f"Error processing frame: {e}")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image data: {str(e)}",
        )

    return {"status": "received"}


@app.get("/api/streams")
async def list_active_streams(current_user: dict = Depends(get_current_user)):
    """
    List all active video streams

    Returns:
        dict: Active stream IDs and their last frame time
    """
    result = {}
    current_time = time.time()

    with stream_lock:
        for stream_id, stream_data in active_streams.items():
            # Consider a stream active if it received a frame in the last 30 seconds
            if current_time - stream_data["last_frame"] < 30:
                result[stream_id] = {
                    "last_frame": stream_data["last_frame"],
                    "active_since": current_time - stream_data["last_frame"],
                }

    return result


@app.get("/api/stream/{stream_id}")
async def get_stream_feed(
    stream_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Get stream analysis data without video frames

    Args:
        stream_id: ID of the stream

    Returns:
        dict: Analysis data for the stream
    """
    if stream_id not in active_streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stream not found or inactive"
        )

    return active_streams[stream_id]["analysis"]


@app.get("/api/stream/{stream_id}")
async def get_video_stream(
    stream_id: str, current_user: dict = Depends(get_current_user)
):
    """
    Stream video frames as MJPEG stream

    Args:
        stream_id: ID of the stream

    Returns:
        StreamingResponse: MJPEG video stream
    """
    return StreamingResponse(
        stream_frames_generator(stream_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


# URL for direct access to the video stream (no auth, only API key)
@app.get("/api/public-stream/{stream_id}/{api_key}")
async def get_public_video_stream(stream_id: str, api_key: str):
    """
    Public endpoint for viewing a stream without authentication
    Requires API key in the URL

    Args:
        stream_id: ID of the stream
        api_key: API key for authentication

    Returns:
        StreamingResponse: MJPEG video stream
    """
    if api_key != RASPI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key"
        )

    return StreamingResponse(
        stream_frames_generator(stream_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/raspi/upload_frame")
async def upload_frame(stream_id: str = Form(...), frame: UploadFile = File(...)):
    """
    Endpoint for Raspberry Pi to upload video frames directly from PiCamera

    Args:
        stream_id: Identifier for the camera/stream
        frame: Image file uploaded from the Raspberry Pi

    Returns:
        dict: Status response
    """
    try:
        # Read the frame data
        img_bytes = await frame.read()

        # Process with DeepFace (placeholder for now)
        try:
            # Convert bytes to image for analysis
            img = Image.open(io.BytesIO(img_bytes))
            frame_array = np.array(img)

            # Analyze with DeepFace (placeholder)
            analysis = deepface_analyze(frame_array)

            # Store the active stream information
            with stream_lock:
                active_streams[stream_id] = {
                    "last_frame": time.time(),
                    "analysis": analysis,
                }

                # Add frame to the stream's frame queue
                if stream_id not in stream_frames:
                    stream_frames[stream_id] = deque(maxlen=30)  # Store last 30 frames
                stream_frames[stream_id].append(img_bytes)

            return {"status": "received", "analysis": "success"}

        except Exception as e:
            print(f"Error processing frame: {e}")
            return {"status": "received", "analysis": "failed", "error": str(e)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image data: {str(e)}",
        )


# Root endpoint for testing
@app.get("/")
async def root():
    return {"message": "Welcome to the Roast Bot API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
