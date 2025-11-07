"""Whisper API client for audio transcription."""
from __future__ import annotations
import os
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def transcribe_audio_file(audio_path: Path, api_token: Optional[str] = None, whisper_model: Optional[str] = None) -> Dict[str, Any]:
    """Send an audio file to Whisper API and parse response."""
    token = api_token or os.getenv('AI_PORTAL_TOKEN')
    if not token:
        logger.error("AI_PORTAL_TOKEN not set")
        return {"success": False, "error": "AI_PORTAL_TOKEN not set (required for Whisper API)"}

    endpoint = os.getenv('LLM_ENDPOINT', 'https://ai.dragonflygroup.fr')
    parsed = urlparse(endpoint)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    url = f"{base_url}/api/v1/audio/transcriptions"

    logger.info(f"Transcribing audio: {audio_path.name} ({audio_path.stat().st_size / 1024:.1f} KB)")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        with open(audio_path, 'rb') as f:
            files = {'audioFile': (audio_path.name, f, 'audio/mpeg')}
            data = {}
            if whisper_model:
                data["model"] = whisper_model

            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=300,
                verify=False  # dev env only
            )

        if response.status_code == 401:
            logger.error("Whisper API: Unauthorized (invalid token)")
            return {"success": False, "error": "Unauthorized: Invalid or missing API key"}

        if response.status_code != 200:
            logger.error(f"Whisper API error {response.status_code}: {response.text[:200]}")
            return {"success": False, "error": f"Whisper API error {response.status_code}: {response.text}"}

        try:
            data = response.json()
            logger.info(f"Whisper API response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        except Exception as e:
            logger.error(f"Failed to parse Whisper API JSON response: {e}")
            return {"success": False, "error": f"Invalid JSON response from Whisper API: {str(e)}"}

        transcription = data.get('text') or data.get('transcription') if isinstance(data, dict) else None
        if transcription is None:
            logger.warning(f"Whisper API returned no text/transcription for {audio_path.name}. Response: {data}")
            return {"success": True, "transcription": "", "empty": True}

        transcription = transcription.strip() if isinstance(transcription, str) else ""
        if not transcription:
            logger.info(f"Empty transcription for {audio_path.name}")
            return {"success": True, "transcription": "", "empty": True}

        logger.info(f"Transcription OK: {len(transcription)} chars")
        return {"success": True, "transcription": transcription}

    except requests.exceptions.Timeout:
        logger.error(f"Whisper API timeout (>5min) for {audio_path.name}")
        return {"success": False, "error": "Whisper API timeout (>5 minutes)"}
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {str(e)}")
        return {"success": False, "error": f"HTTP request failed: {str(e)}"}
    except Exception as e:
        logger.exception(f"Transcription error for {audio_path.name}")
        return {"success": False, "error": f"Transcription error: {str(e)}"}
