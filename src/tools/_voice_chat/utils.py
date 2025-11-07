"""Utils for voice_chat: portal base, chroot IO, ffprobe, conversion, MCP call, small helpers."""
from __future__ import annotations
import os, base64, json, subprocess, uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from urllib.parse import urlparse

# --- Project paths ---

def get_project_root() -> Path:
    cur = Path(__file__).resolve()
    while cur != cur.parent:
        if (cur / 'pyproject.toml').exists() or (cur / '.git').exists():
            return cur
        cur = cur.parent
    return Path.cwd()


def abs_from_project(rel_path: str) -> Path:
    return get_project_root() / rel_path


# --- Portal base URL from LLM_ENDPOINT ---

def portal_base_from_llm_endpoint() -> str:
    endpoint = os.getenv("LLM_ENDPOINT", "https://ai.dragonflygroup.fr")
    parsed = urlparse(endpoint)
    return f"{parsed.scheme}://{parsed.netloc}"


def portal_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


# --- Audio IO in chroot (docs/audio/tmp) ---

def ensure_audio_tmp_dir() -> Path:
    p = abs_from_project("docs/audio/tmp")
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_audio_from_b64_chroot(b64: str, mime: Optional[str]) -> Path:
    # Accept data URLs or pure base64
    if "base64," in b64:
        b64 = b64.split("base64,", 1)[1]
    raw = base64.b64decode(b64)
    out_dir = ensure_audio_tmp_dir()
    # Default to webm if mime is unknown
    suffix = ".webm"
    if mime:
        m = mime.lower()
        if "wav" in m: suffix = ".wav"
        elif "ogg" in m: suffix = ".ogg"
        elif "mpeg" in m or "mp3" in m: suffix = ".mp3"
        elif "webm" in m: suffix = ".webm"
    fname = f"utter_{uuid.uuid4().hex}{suffix}"
    out_path = out_dir / fname
    out_path.write_bytes(raw)
    return out_path


def probe_audio_duration(path: Path) -> Optional[float]:
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return None
        return float(json.loads(r.stdout).get("format", {}).get("duration", 0.0))
    except Exception:
        return None


def convert_to_mp3_16k_mono(src: Path) -> Dict[str, Any]:
    """Convert any audio file to MP3 16kHz mono using ffmpeg."""
    try:
        out_dir = src.parent
        out_path = out_dir / f"{src.stem}_16k_mono.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-i", str(src),
            "-ar", "16000",
            "-ac", "1",
            "-acodec", "libmp3lame",
            "-q:a", "2",
            str(out_path)
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return {"success": False, "error": f"ffmpeg convert failed: {r.stderr[:200]}"}
        if not out_path.exists() or out_path.stat().st_size == 0:
            return {"success": False, "error": "ffmpeg conversion produced no output"}
        return {"success": True, "path": out_path}
    except FileNotFoundError:
        return {"success": False, "error": "ffmpeg not found (install FFmpeg)"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ffmpeg conversion timeout"}
    except Exception as e:
        return {"success": False, "error": f"conversion error: {e}"}


# --- MCP /execute call to call_llm ---

def mcp_base() -> str:
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = os.getenv("MCP_PORT", "8000")
    return f"http://{host}:{port}"


def call_llm_via_mcp(messages: List[Dict[str, str]], model: Optional[str], temperature: float, max_tokens: int) -> Dict[str, Any]:
    payload = {
        "tool": "call_llm",
        "params": {
            "messages": messages,
            "model": model or os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"),
            "temperature": temperature,
            "max_tokens": int(max_tokens)
        }
    }
    try:
        # Always log full payload when debug is enabled
        mode = os.getenv("VOICE_CHAT_DEBUG", "0").lower()
        if mode not in ("0", "false", "no", ""):
            print(json.dumps({"event":"voice_chat_llm_payload","payload":payload}, ensure_ascii=False))
        r = requests.post(f"{mcp_base()}/execute", json=payload, timeout=120)
        if r.status_code != 200:
            return {"error": f"call_llm failed {r.status_code}: {r.text[:200]}"}
        data = r.json()
        text = None
        if isinstance(data, dict):
            text = data.get("result") or data.get("text") or data.get("content")
            if isinstance(text, dict):
                text = text.get("text") or text.get("content")
        return {"success": True, "assistant_text": text or ""}
    except Exception as e:
        return {"error": f"MCP /execute call_llm error: {e}"}


# --- Debug helpers (only new message + full CALL LLM) ---

def debug_log_llm_call(messages: List[Dict[str, str]], model: Optional[str], temperature: float, max_tokens: int) -> None:
    mode = os.getenv("VOICE_CHAT_DEBUG", "0").lower()
    if mode in ("0", "false", "no", ""):
        return
    try:
        last = messages[-1] if messages else {"role": "?", "content": ""}
        print(json.dumps({
            "event": "voice_chat_new_message",
            "role": last.get("role"),
            "content": last.get("content", ""),
        }, ensure_ascii=False))
    except Exception:
        pass
