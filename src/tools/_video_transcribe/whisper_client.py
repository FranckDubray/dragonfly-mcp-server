"""Whisper API client for audio transcription."""
from __future__ import annotations
import os
import requests
from pathlib import Path
from typing import Dict, Any


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
    
    # API endpoint
    endpoint = os.getenv('LLM_ENDPOINT', 'https://ai.dragonflygroup.fr')
    if not endpoint.endswith('/'):
        endpoint += '/'
    url = f"{endpoint}api/v1/audio/transcriptions"
    
    # Headers
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # Open file and send multipart request
        with open(audio_path, 'rb') as f:
            files = {'audioFile': (audio_path.name, f, 'audio/mpeg')}
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=300  # 5 minutes timeout
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
        transcription = data.get('transcription', '')
        
        if not transcription:
            return {
                "success": False,
                "error": "Empty transcription received from API"
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
