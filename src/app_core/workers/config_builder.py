"""
Config Builder : construit la config Realtime pour un worker
DB-first avec fallback .env (hybride, robuste)
- Les valeurs peuvent venir de la DB (job_meta) ou de l'environnement (.env)
- Si une clé critique manque à la fois en DB et en env, on lève une erreur explicite
"""
from pathlib import Path
import sqlite3
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SQLITE_DIR = PROJECT_ROOT / "sqlite3"
TOOL_SPECS_DIR = PROJECT_ROOT / "src" / "tool_specs"

def build_realtime_config(worker_id: str) -> dict:
    """Construit la configuration complète pour session Realtime (DB d'abord, fallback .env).

    Clés critiques minimales:
      - api_base (ou llm_endpoint, ou env LLM_ENDPOINT)
      - token (api_token/token, ou env AI_PORTAL_TOKEN)
      - model (realtime_model, ou env REALTIME_MODEL)

    Le reste a des valeurs par défaut sûres si absent.
    """
    meta = _load_worker_meta(worker_id)

    # API base (DB → env)
    api_base = _resolve_api_base(meta)
    if not api_base:
        raise RuntimeError("Missing api_base/llm_endpoint (DB) or LLM_ENDPOINT (.env)")

    # Token (DB → env)
    token = (meta.get('api_token') or meta.get('token') or os.getenv('AI_PORTAL_TOKEN', '')).strip()
    if not token:
        raise RuntimeError("Missing api_token/token (DB) or AI_PORTAL_TOKEN (.env)")

    # Model (DB → env)
    model = (meta.get('realtime_model') or os.getenv('REALTIME_MODEL', '')).strip()
    if not model:
        raise RuntimeError("Missing realtime_model (DB) or REALTIME_MODEL (.env)")

    # Persona & instructions (DB → fallback auto enrichi)
    persona = (meta.get('persona') or f"Je suis {worker_id}.").strip()
    instructions = (meta.get('instructions') or _build_instructions(worker_id, meta)).strip()

    # Tools (DB → fallback worker_query)
    tools = _resolve_tools(meta)

    # Audio & generation params (DB → défauts sûrs)
    voice = (meta.get('voice') or 'alloy').strip()
    temperature = _safe_float(meta.get('temperature'), 0.8)
    modalities = _get_meta_json(meta, 'modalities_json', default=["text", "audio"]) or ["text", "audio"]
    turn_detection = _get_meta_json(meta, 'turn_detection_json', default={
        "type": "server_vad",
        "threshold": 0.5,
        "prefix_padding_ms": 300,
        "silence_duration_ms": 1400,
    })
    input_audio_format = (meta.get('input_audio_format') or 'pcm16').strip()
    output_audio_format = (meta.get('output_audio_format') or 'pcm16').strip()

    logger.info(f"Realtime config (DB+env): api_base={api_base}, model={model}, voice={voice}")

    return {
        "worker_id": worker_id,
        "worker_name": meta.get('worker_name', worker_id.capitalize()),
        "api_base": api_base,
        "token": token,
        "model": model,
        "persona": persona,
        "instructions": instructions,
        "tools": tools,
        "voice": voice,
        "avatar_url": meta.get('avatar_url'),  # pour UI inline
        "temperature": temperature,
        "modalities": modalities,
        "turn_detection": turn_detection,
        "input_audio_format": input_audio_format,
        "output_audio_format": output_audio_format,
    }

def _safe_float(v, default):
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _resolve_api_base(meta: Dict[str, Any]) -> str:
    """Résout l'api_base depuis DB (api_base/llm_endpoint) ou .env LLM_ENDPOINT, en normalisant l'URL."""
    # 1) DB: api_base direct
    api_base = str(meta.get('api_base') or '').rstrip('/')
    if api_base:
        return api_base

    # 2) DB: llm_endpoint
    endpoint = str(meta.get('llm_endpoint') or '').rstrip('/')
    # 3) env: LLM_ENDPOINT
    if not endpoint:
        endpoint = os.getenv('LLM_ENDPOINT', '').rstrip('/')

    if not endpoint:
        return ''

    if "/chat/completions" in endpoint:
        return endpoint.replace("/chat/completions", "")
    elif "/api/v1/" in endpoint:
        return endpoint.split("/api/v1/")[0] + "/api/v1"
    elif endpoint.endswith("/api/v1"):
        return endpoint
    else:
        return endpoint


def _load_worker_meta(worker_id: str) -> dict:
    """Charge toutes les métadonnées depuis job_meta (DB)."""
    # Recherche case-insensitive (alain ou Alain)
    db_path: Optional[Path] = None
    for pattern in [f"worker_{worker_id}.db", f"worker_{worker_id.capitalize()}.db"]:
        test_path = SQLITE_DIR / pattern
        if test_path.exists():
            db_path = test_path
            break

    if not db_path:
        raise FileNotFoundError(f"Worker {worker_id} not found in {SQLITE_DIR}")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
    cursor = conn.cursor()

    cursor.execute("SELECT skey, svalue FROM job_meta")
    rows = cursor.fetchall()
    conn.close()

    return {row[0]: row[1] for row in rows}


def _get_meta_json(meta: dict, key: str, default=None):
    val = meta.get(key)
    if not val:
        return default
    try:
        return json.loads(val)
    except Exception:
        logger.warning(f"Invalid JSON in job_meta['{key}']")
        return default


def _resolve_tools(meta: dict) -> list:
    """Résout la liste des tools depuis job_meta.tools_json (si présent), sinon fallback worker_query. """
    tools_json = _get_meta_json(meta, 'tools_json', default=None)
    resolved = []

    def add_worker_query():
        try:
            resolved.append(_load_worker_query_tool_spec())
        except Exception as e:
            logger.error(f"Failed to load worker_query tool spec: {e}")

    if isinstance(tools_json, list) and tools_json:
        for item in tools_json:
            if isinstance(item, str):
                if item == 'worker_query':
                    add_worker_query()
                else:
                    logger.warning(f"Unknown tool name in DB: {item} (ignored)")
            elif isinstance(item, dict):
                if item.get('type') == 'function' and item.get('name') and item.get('parameters'):
                    resolved.append(item)
                else:
                    logger.warning("Invalid tool spec in DB (ignored)")
    else:
        add_worker_query()

    if not resolved:
        add_worker_query()

    return resolved


def _load_worker_query_tool_spec() -> dict:
    """Charge le spec worker_query (read-only)."""
    spec_path = TOOL_SPECS_DIR / "worker_query.json"

    if not spec_path.exists():
        raise FileNotFoundError(f"worker_query.json spec not found at {spec_path}")

    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)

    tool = {
        "type": "function",
        "name": spec["function"]["name"],
        "description": spec["function"].get("description", ""),
        "parameters": spec["function"]["parameters"]
    }

    return tool


def _build_instructions(worker_id: str, meta: dict) -> str:
    """Fallback: construit des instructions système FR enrichies depuis la DB si 'instructions' absent.

    Combine: persona, identité du worker (nom, métier), employeur.
    """
    worker_name = meta.get('worker_name', worker_id.capitalize()).strip()
    persona = (meta.get('persona') or f"Je suis {worker_name}.").strip()
    job = (meta.get('job') or '').strip()
    employeur = (meta.get('employeur') or '').strip()
    employe_depuis = (meta.get('employe_depuis') or '').strip()
    email = (meta.get('email') or '').strip()
    timezone_s = (meta.get('timezone') or '').strip()
    bio = (meta.get('bio') or '').strip()
    tags = _get_meta_json(meta, 'tags_json', default=None)
    client_info = meta.get('client_info')

    # Date FR (UTC simplifié)
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A %d %B %Y")
    time_str = now.strftime("%H:%M")
    jours = {
        'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
    }
    mois = {
        'January': 'Janvier', 'February': 'Février', 'March': 'Mars', 'April': 'Avril',
        'May': 'Mai', 'June': 'Juin', 'July': 'Juillet', 'August': 'Août',
        'September': 'Septembre', 'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'
    }
    for en, fr in jours.items():
        date_str = date_str.replace(en, fr)
    for en, fr in mois.items():
        date_str = date_str.replace(en, fr)

    identite_section = f"""
IDENTITÉ DU WORKER
Tu t'appelles {worker_name}.
{('Métier : ' + job + '\n') if job else ''}{('Employeur : ' + employeur + (' (depuis ' + employe_depuis + ')') if employe_depuis else '') + '\n' if employeur else ''}
"""

    bio_section = f"Bio : {bio}\n" if bio else ""
    tags_section = f"Tags : {', '.join(tags)}\n" if isinstance(tags, list) and tags else ""

    client_section = ""
    if client_info:
        client_section = f"""
MON CLIENT
Je travaille pour : {client_info}
Relation client :
- Ton professionnel et accessible
- Adapter les réponses au contexte (âge/localisation)
"""

    return f"""
🇫🇷 Parler en français.

CONTEXTE
Nous sommes le {date_str}. Il est {time_str} (heure de Paris).

{persona}
{client_section}
{identite_section}
OUTILS
- Tu as accès au tool worker_query (lecture seule). Utilise uniquement des SELECT
- Limite les résultats (paramètre limit)

STYLE
- Première personne, concis et factuel
- Si incertain : le dire clairement
- Si erreur requête : informer calmement
"""
