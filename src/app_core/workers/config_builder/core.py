import os, logging
from typing import Any, Dict
from .meta import load_worker_meta, get_meta_json, resolve_api_base
from .tools import resolve_tools
from .instructions import build_base_instructions
from app_core.workers.prompts.worker_query_prompt import build_worker_query_prompt
from app_core.workers.prompts.dynamic_schema import build_dynamic_schema_section, build_process_data_section
from app_core.workers.prompts.process_sections import build_process_mermaid_section

logger = logging.getLogger(__name__)


def build_realtime_config(worker_id: str) -> dict:
    meta = load_worker_meta(worker_id)

    api_base = resolve_api_base(meta)
    if not api_base:
        raise RuntimeError("Missing api_base/llm_endpoint (DB) or LLM_ENDPOINT (.env)")

    token = (meta.get('api_token') or meta.get('token') or os.getenv('AI_PORTAL_TOKEN', '')).strip()
    if not token:
        raise RuntimeError("Missing api_token/token (DB) or AI_PORTAL_TOKEN (.env)")

    model = (meta.get('realtime_model') or os.getenv('REALTIME_MODEL', '')).strip()
    if not model:
        raise RuntimeError("Missing realtime_model (DB) or REALTIME_MODEL (.env)")

    base_instructions = meta.get('instructions') or build_base_instructions(worker_id, meta)
    static_prompt = build_worker_query_prompt()

    try:
        dynamic_schema = build_dynamic_schema_section(worker_id)
    except Exception as e:
        dynamic_schema = ""
        logger.warning(f"Failed to append dynamic schema section: {e}")
    try:
        process_section = build_process_mermaid_section(worker_id)
    except Exception as e:
        process_section = ""
        logger.warning(f"Failed to append process Mermaid section: {e}")
    try:
        process_data_section = build_process_data_section(worker_id)
    except Exception as e:
        process_data_section = ""
        logger.warning(f"Failed to append process data section: {e}")

    instructions = (base_instructions.strip() + "\n\n" + static_prompt +
                    (("\n\n" + dynamic_schema) if dynamic_schema else "") +
                    (("\n\n" + process_section) if process_section else "") +
                    (("\n\n" + process_data_section) if process_data_section else ""))

    tools = resolve_tools(meta)

    voice = (meta.get('voice') or 'alloy').strip()
    try:
        temperature = float(meta.get('temperature') or 0.8)
    except Exception:
        temperature = 0.8
    modalities = get_meta_json(meta, 'modalities_json', default=["text","audio"]) or ["text","audio"]
    turn_detection = get_meta_json(meta, 'turn_detection_json', default={
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
        "persona": meta.get('persona') or f"Je suis {worker_id}.",
        "instructions": instructions,
        "tools": tools,
        "voice": voice,
        "avatar_url": meta.get('avatar_url'),
        "temperature": temperature,
        "modalities": modalities,
        "turn_detection": turn_detection,
        "input_audio_format": input_audio_format,
        "output_audio_format": output_audio_format,
    }
