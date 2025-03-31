#!/usr/bin/env python3
"""
Raspberry Pi Client for Roast Bot

This script requests a roast from the Roast Bot API and plays it.
It's designed to be run on a Raspberry Pi with a speaker connected.

Requirements:
- requests
- python-dotenv
- pygame (for audio playback)

Usage:
python raspi_client.py [name] [voice_id]
"""

import os
import json
import time
import requests
import argparse
from dotenv import load_dotenv
import pygame

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("RASPI_API_KEY", "raspberry_secret_key")
USER_ID = os.getenv("USER_ID", "")  # Set this to a valid user ID
TEMP_AUDIO_FILE = "temp_roast.mp3"

# Available voices
AVAILABLE_VOICES = {
    "male1": "jsCqWAovK2LkecY7zXl4",
    "male2": "pNInz6obpgDQGcFmaJgB",
    "female1": "21m00Tcm4TlvDq8ikWAM",
    "female2": "AZnzlk1XvdvUeBnXmlld",
    "villain": "VR6AewLTigWG4xSOukaG",
    "deep": "2EiwWnXFnvU5JabPnv8n"
}

DEFAULT_VOICE = "villain"  # Default to villain voice for a roast

def setup_audio():
    """Initialize audio playback"""
    pygame.mixer.init()
    pygame.init()

def trigger_roast(name, voice_id=None):
    """
    Request a roast from the API and save it as an audio file
    
    Args:
        name (str): The name of the person to roast
        voice_id (str, optional): The voice ID to use, or a key from AVAILABLE_VOICES
        
    Returns:
        bool: True if successful, False otherwise
    """
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # If voice_id is a key in our dictionary, get the actual ID
    if voice_id in AVAILABLE_VOICES:
        voice_id = AVAILABLE_VOICES[voice_id]
    
    payload = {
        "user_id": USER_ID,
        "name": name
    }
    
    # Add voice_id if provided
    if voice_id:
        payload["voice_id"] = voice_id
    
    try:
        # Request the roast
        response = requests.post(
            f"{API_URL}/api/raspi/trigger-roast", 
            headers=headers,
            json=payload
        )
        
        # Check if request was successful
        if response.status_code == 200:
            # Check content type to see if we got audio back
            content_type = response.headers.get("Content-Type", "")
            
            if "audio" in content_type:
                # Save the audio to a file
                with open(TEMP_AUDIO_FILE, "wb") as f:
                    f.write(response.content)
                return True
            else:
                # We got JSON response (fallback text)
                print("Received text fallback instead of audio")
                data = response.json()
                print(f"Roast text: {data.get('roast')}")
                print(f"Error: {data.get('error')}")
                return False
        else:
            print(f"Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"API Error: {error_data.get('detail', 'Unknown error')}")
            except:
                print(f"API Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Request failed: {e}")
        return False

def play_audio():
    """Play the roast audio file"""
    try:
        pygame.mixer.music.load(TEMP_AUDIO_FILE)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    except Exception as e:
        print(f"Playback error: {e}")

def cleanup():
    """Clean up resources"""
    pygame.mixer.quit()
    pygame.quit()
    
    # Remove temporary audio file
    if os.path.exists(TEMP_AUDIO_FILE):
        os.remove(TEMP_AUDIO_FILE)

def list_voices():
    """Print available voices"""
    print("Available voices:")
    for key, voice_id in AVAILABLE_VOICES.items():
        print(f"  {key}: {voice_id}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Raspberry Pi Roast Bot Client")
    parser.add_argument("name", nargs="?", default="Guest", help="Name of the person to roast")
    parser.add_argument("--voice", "-v", default=DEFAULT_VOICE, help="Voice to use (name or ID)")
    parser.add_argument("--list-voices", "-l", action="store_true", help="List available voices")
    
    args = parser.parse_args()
    
    if args.list_voices:
        list_voices()
        return
    
    setup_audio()
    
    try:
        print(f"Requesting roast for {args.name} with voice {args.voice}...")
        
        # Request and save the roast
        if trigger_roast(args.name, args.voice):
            print("Playing roast...")
            play_audio()
        else:
            print("Failed to get roast")
            
    finally:
        cleanup()

if __name__ == "__main__":
    main() 