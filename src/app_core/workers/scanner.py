









"""
Scanner workers : découverte automatique worker_*.db
"""
from pathlib import Path
import sqlite3
import logging
import json as _json

logger = logging.getLogger(__name__)

# Chemin ABSOLU depuis src/app_core/workers/ → racine/sqlite3/
# src/app_core/workers/scanner.py → ../../.. = racine projet
SQLITE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sqlite3"

def scan_workers() -> list:
    """
    Scan sqlite3/ pour découvrir tous les worker_*.db
    
    Returns:
        Liste de dicts: [{
          "id": "alain", "name": "Alain", "voice": "ash",
          "avatar_url": "https://...", "statut": "...",
          "job": "...", "employeur": "...", "employe_depuis": "...",
          "gallery": ["https://...", ...],
          # Champs optionnels (si présents dans job_meta):
          "email": str,
          "bio": str,
          "tags": list[str],                # depuis tags_json
          "video_teaser_url": str,
          "video_teaser_poster": str,
          "timezone": str,
          "working_hours": str,
          "kpis": dict,                     # depuis kpis_json
          "recent_tools": list,             # depuis recent_tools_json
          "recent_transcripts": list,       # depuis recent_transcripts_json
          "latency_hint_ms": float|int,
        }]
    """
    if not SQLITE_DIR.exists():
        logger.warning(f"SQLite dir not found: {SQLITE_DIR}")
        return []
    
    logger.info(f"📁 Scanning workers in: {SQLITE_DIR}")
    
    workers = []
    
    for db_file in SQLITE_DIR.glob("worker_*.db"):
        # ✅ Extraire l'ID du worker depuis le nom de fichier
        # Exemple : worker_Alain.db → alain (minuscule pour uniformité)
        worker_id = db_file.stem.replace("worker_", "").lower()
        
        logger.info(f"🔍 Found DB file: {db_file.name} → ID: '{worker_id}'")
        
        try:
            meta = _get_worker_meta(db_file)
            
            # Convert JSON helpers
            def _loads(key):
                v = meta.get(key)
                if not v:
                    return None
                try:
                    return _json.loads(v)
                except Exception:
                    logger.warning(f"Invalid JSON in {db_file.name} job_meta['{key}']")
                    return None
            
            # Galerie optionnelle (JSON string → list)
            gallery = _loads("gallery_json") or _loads("gallery")
            if gallery is not None and not isinstance(gallery, list):
                gallery = None
            
            # Champs optionnels enrichis
            tags = _loads("tags_json")
            if tags is not None and not isinstance(tags, list):
                tags = None
            kpis = _loads("kpis_json")
            if kpis is not None and not isinstance(kpis, dict):
                kpis = None
            recent_tools = _loads("recent_tools_json")
            if recent_tools is not None and not isinstance(recent_tools, list):
                recent_tools = None
            recent_transcripts = _loads("recent_transcripts_json")
            if recent_transcripts is not None and not isinstance(recent_transcripts, list):
                recent_transcripts = None
            
            def _num(v):
                try:
                    return float(v) if v is not None else None
                except Exception:
                    return None
            
            workers.append({
                "id": worker_id,
                "name": meta.get("worker_name", worker_id.capitalize()),
                "voice": meta.get("voice", "alloy"),
                "avatar_url": meta.get("avatar_url"),  # ✅ URL avatar
                "statut": meta.get("statut"),          # ✅ Statut
                "job": meta.get("job"),                # ✅ Métier
                "employeur": meta.get("employeur"),    # ✅ Employeur
                "employe_depuis": meta.get("employe_depuis"),  # ✅ Employé depuis
                "gallery": gallery,                    # ✅ Galerie d'images
                "has_persona": bool(meta.get("persona")),
                "db_path": str(db_file),
                "db_size": db_file.stat().st_size,
                # Enrichissements optionnels 100% DB
                "email": meta.get("email"),
                "bio": meta.get("bio"),
                "tags": tags,
                "video_teaser_url": meta.get("video_teaser_url"),
                "video_teaser_poster": meta.get("video_teaser_poster"),
                "timezone": meta.get("timezone"),
                "working_hours": meta.get("working_hours"),
                "kpis": kpis,
                "recent_tools": recent_tools,
                "recent_transcripts": recent_transcripts,
                "latency_hint_ms": _num(meta.get("latency_hint_ms")),
            })
            
            logger.info(f"✅ Worker loaded: {worker_id} ({meta.get('worker_name', 'N/A')})")
            
        except Exception as e:
            logger.warning(f"❌ Failed to load worker {worker_id}: {e}")
            continue
    
    logger.info(f"📊 Total workers found: {len(workers)}")
    
    # Tri alphabétique par nom
    return sorted(workers, key=lambda w: w["name"])

def _get_worker_meta(db_path: Path) -> dict:
    """
    Charge métadonnées depuis job_meta
    
    Args:
        db_path: Chemin vers worker_*.db
        
    Returns:
        Dict {skey: svalue} de job_meta
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=2.0)
    cursor = conn.cursor()
    
    cursor.execute("SELECT skey, svalue FROM job_meta")
    rows = cursor.fetchall()
    
    conn.close()
    
    return {row[0]: row[1] for row in rows}

 
 
 
 
 
 
 
 
 
 
 
