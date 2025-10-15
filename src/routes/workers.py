
"""
Routes Workers Realtime
Endpoints pour interface vocale workers
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
import httpx
import json

from app_core.workers import (
    scan_workers,
    build_realtime_config,
    query_worker_db
)
from app_core.safe_json import SafeJSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workers", tags=["workers"])

@router.get("")
async def list_workers(request: Request):
    """Liste tous les workers disponibles"""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return RedirectResponse(url="/workers/ui", status_code=302)
    
    try:
        workers = scan_workers()
        # Filtrer champs sensibles non nécessaires au frontend
        public = []
        for w in workers:
            w2 = dict(w)
            w2.pop("db_path", None)
            w2.pop("db_size", None)
            public.append(w2)
        return SafeJSONResponse(content={
            "workers": public,
            "count": len(public)
        })
    except Exception as e:
        logger.exception("Failed to scan workers")
        raise HTTPException(500, f"Scan failed: {str(e)}")

@router.get("/ui", response_class=HTMLResponse)
async def workers_ui():
    """Page UI Workers Realtime"""
    from templates.workers_page import WORKERS_HTML
    return HTMLResponse(content=WORKERS_HTML)

@router.get("/{name}/realtime/config")
async def get_worker_realtime_config(name: str):
    """Récupère la configuration Realtime pour un worker (token redacted)."""
    try:
        config = build_realtime_config(name)
        # 🔒 Ne pas exposer le token au frontend
        redacted = dict(config)
        if "token" in redacted:
            redacted["token"] = "***"
        return SafeJSONResponse(content=redacted)
        
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(500, f"Config error: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to get config for worker {name}")
        raise HTTPException(500, f"Internal error: {str(e)}")

@router.post("/{name}/realtime/start")
async def start_realtime_session(name: str):
    """Démarre une session Realtime via le backend (proxy pour éviter CORS)"""
    try:
        logger.info(f"[REALTIME START] Worker: {name}")
        
        # Charger config worker (DB -> env)
        config = build_realtime_config(name)
        logger.info(f"[REALTIME CONFIG] Model: {config['model']}, Voice: {config['voice']}")
        
        # Préparer body pour POST /realtime/sessions
        # ✅ INCLURE tools et tool_choice dès le départ
        session_body = {
            "model": config["model"],
            "modalities": config["modalities"],
            "voice": config["voice"],  # ✅ VOIX ENVOYÉE ICI
            "instructions": config["instructions"],
            "temperature": config["temperature"],
            "input_audio_format": config["input_audio_format"],
            "output_audio_format": config["output_audio_format"],
            "tools": config["tools"],
            "tool_choice": "auto"
        }
        
        # Ajouter turn_detection si présent
        if "turn_detection" in config:
            session_body["turn_detection"] = config["turn_detection"]
        
        # POST vers Portal AI
        session_url = f"{config['api_base']}/realtime/sessions"
        
        logger.info(f"[REALTIME REQUEST] URL: {session_url}")
        logger.info(f"[REALTIME REQUEST] Voice: {config['voice']}")  # ✅ LOG AJOUTÉ
        logger.info(f"[REALTIME REQUEST] Tools count: {len(config['tools'])}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                session_url,
                json=session_body,
                headers={
                    "Authorization": f"Bearer {config['token']}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            logger.info(f"[REALTIME RESPONSE] Status: {response.status_code}")
            
            if not response.is_success:
                error_text = response.text
                logger.error(f"[REALTIME RESPONSE] Error: {error_text}")
                raise HTTPException(response.status_code, f"Portal error: {error_text}")
            
            session_data = response.json()
        
        # Logger la réponse
        logger.info(f"[REALTIME RESPONSE] Session ID: {session_data.get('id')}")
        logger.info(f"[REALTIME RESPONSE] Voice returned: {session_data.get('voice', 'NOT_IN_RESPONSE')}")  # ✅ LOG AJOUTÉ
        
        # Vérifier les clés essentielles
        if not session_data.get('id'):
            raise HTTPException(500, f"Invalid Portal response: missing 'id'")
        
        if not session_data.get('websocketUrl'):
            raise HTTPException(500, f"Invalid Portal response: missing 'websocketUrl'")
        
        if not session_data.get('sessionToken'):
            raise HTTPException(500, f"Invalid Portal response: missing 'sessionToken'")
        
        # ✅ Ajouter des infos utiles pour le frontend (sans token)
        session_data["voice"] = config["voice"]
        session_data["tools"] = config["tools"]
        session_data["turn_detection"] = config.get("turn_detection", {
            "type": "server_vad",
            "threshold": 0.5,
            "prefix_padding_ms": 300,
            "silence_duration_ms": 1000
        })
        session_data["instructions"] = config.get("instructions", "")
        
        logger.info(f"[REALTIME SUCCESS] Session created: {session_data.get('id')}")
        
        return SafeJSONResponse(content=session_data)
        
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(500, f"Config error: {str(e)}")
    except httpx.HTTPError as e:
        logger.exception(f"HTTP error calling Portal API")
        raise HTTPException(500, f"Portal communication error: {str(e)}")
    except Exception as e:
        logger.exception(f"Failed to start realtime session for {name}")
        raise HTTPException(500, f"Internal error: {str(e)}")

@router.post("/{name}/tool/query")
async def execute_worker_query_tool(name: str, request: Request):
    """
    ✅ PROXY SÉCURISÉ pour tool worker_query
    
    Valide et exécute une requête SELECT read-only sur la base du worker.
    Appelé depuis le frontend quand le LLM invoque worker_query.
    """
    try:
        body = await request.json()
        
        # Extraire paramètres (format tool call)
        query = body.get("query", "").strip()
        limit = int(body.get("limit", 50))
        
        if not query:
            logger.warning(f"[TOOL QUERY] {name}: Missing query parameter")
            raise HTTPException(400, "Parameter 'query' is required")
        
        # ✅ Validation : DOIT être un SELECT
        if not query.upper().strip().startswith("SELECT"):
            logger.warning(f"[TOOL QUERY] {name}: Non-SELECT query blocked: {query[:50]}")
            raise HTTPException(400, "Only SELECT queries are allowed")
        
        # Limiter à 100 max
        limit = min(max(1, limit), 100)
        
        logger.info(f"[TOOL QUERY] {name}: Executing query (limit={limit})")
        
        # ✅ Appeler le module sécurisé
        result = query_worker_db(name, query, limit)
        
        # ✅ Retourner format adapté pour LLM (summary présent)
        return SafeJSONResponse(content=result)
        
    except ValueError as e:
        # Validation SQL échouée (query_worker_db)
        logger.warning(f"[TOOL QUERY] {name}: Validation error: {e}")
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        # Worker DB non trouvé
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.exception(f"[TOOL QUERY] {name}: Execution failed")
        raise HTTPException(500, f"Query execution failed: {str(e)}")

@router.post("/{name}/query")
async def query_worker(name: str, request: Request):
    """
    Exécute une requête SQL read-only sur la base du worker
    (Endpoint legacy pour l'UI, pas pour les tools)
    """
    try:
        body = await request.json()
        query = body.get("query", "").strip()
        limit = min(int(body.get("limit", 50)), 200)
        
        if not query:
            raise HTTPException(400, "Query is required")
        
        result = query_worker_db(name, query, limit)
        return SafeJSONResponse(content=result)
        
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.exception(f"Failed to query worker {name}")
        raise HTTPException(500, f"Query failed: {str(e)}")
