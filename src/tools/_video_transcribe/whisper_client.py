"""Whisper API client for audio transcription."""
from __future__ import annotations
import os
import requests
from pathlib import Path
from typing import Dict, Any
from urllib.parse import urlparse


def transcribe_audio_file(audio_path: Path, api_token: str = None) -> Dict[str, Any]:
    """
    Transcribe audio file using Whisper API.
    
    Args:
        audio_path: Path to audio file (MP3)
        api_token: API token (if None, reads from AI_PORTAL_TOKEN env)
        
    Returns:
        Dict with success, transcription, or error
    """
    # Get API token
    token = api_token or os.getenv('AI_PORTAL_TOKEN')
    if not token:
        return {
            "success": False,
            "error": "AI_PORTAL_TOKEN not set (required for Whisper API)"
        }
    
    # API endpoint - extract base URL only (protocol + domain)
    endpoint = os.getenv('LLM_ENDPOINT', 'https://ai.dragonflygroup.fr')
    parsed = urlparse(endpoint)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    url = f"{base_url}/api/v1/audio/transcriptions"
    
    # Headers
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Open file and send multipart request
        with open(audio_path, 'rb') as f:
            files = {'audioFile': (audio_path.name, f, 'audio/mpeg')}
            data = {'model': 'whisper-large-v3'}  # Specify Whisper model
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=300,  # 5 minutes timeout
                verify=False  # Disable SSL verification for dev environment
            )
        
        # Check response status
        if response.status_code == 401:
            return {
                "success": False,
                "error": "Unauthorized: Invalid or missing API key"
            }
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Whisper API error {response.status_code}: {response.text}"
            }
        
        # Parse JSON response
        data = response.json()
        transcription = data.get('transcription', '').strip()
        
        # If transcription is empty (silence/music), return success with empty text
        # This allows the caller to handle it (skip the chunk or keep it)
        if not transcription:
            return {
                "success": True,
                "transcription": "",
                "empty": True  # Flag to indicate this was empty (silence/music)
            }
        
        return {
            "success": True,
            "transcription": transcription
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Whisper API timeout (>5 minutes)"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Transcription error: {str(e)}"
        }
