
"""
DB Query : exécution requêtes SQL read-only sur worker DB
Validation stricte + formatting pour TTS
"""
from pathlib import Path
import sqlite3
import logging
import re

logger = logging.getLogger(__name__)

# Chemin ABSOLU depuis src/app_core/workers/ → racine/sqlite3/
# src/app_core/workers/db_query.py → ..\..\.. = racine projet
SQLITE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sqlite3"

# Liste noire mots-clés SQL
FORBIDDEN_KEYWORDS = [
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
    'PRAGMA', 'ATTACH', 'DETACH', 'VACUUM', 'REPLACE'
]

_LIMIT_CAP = 200


def _cap_limit_in_query(q: str, cap: int = _LIMIT_CAP) -> str:
    """Cappe LIMIT présent dans la requête, ou l'ajoute si absent."""
    q_stripped = q.rstrip().rstrip(';')
    m = re.search(r"\bLIMIT\s+(\d+)\b", q_stripped, flags=re.IGNORECASE)
    if m:
        try:
            n = int(m.group(1))
        except Exception:
            n = cap
        if n > cap:
            q_stripped = re.sub(r"\bLIMIT\s+\d+\b", f"LIMIT {cap}", q_stripped, flags=re.IGNORECASE)
        return q_stripped
    return f"{q_stripped} LIMIT {cap}"


def query_worker_db(worker_id: str, query: str, limit: int = 50) -> dict:
    """
    Exécute une requête SELECT read-only sur worker DB
    
    Args:
        worker_id: Identifiant worker (ex: "alain", pas "worker_alain")
        query: Requête SQL (SELECT uniquement)
        limit: Limite de résultats (max 200)
        
    Returns:
        Dict avec success, rows, count, summary (formatted pour TTS)
        
    Raises:
        ValueError: Si query invalide
        FileNotFoundError: Si worker DB n'existe pas
        sqlite3.Error: Si erreur SQL
    """
    # Validation query
    _validate_query(query)
    
    # Limiter résultats (cap global, y compris si LIMIT déjà présent)
    cap = min(max(1, limit), _LIMIT_CAP)
    
    # ✅ Vérifier DB existe (avec ou sans majuscule) - LOG SUPPRIMÉ
    db_path = None
    for pattern in [f"worker_{worker_id}.db", f"worker_{worker_id.capitalize()}.db"]:
        test_path = SQLITE_DIR / pattern
        if test_path.exists():
            db_path = test_path
            break
    
    if not db_path:
        logger.error(f"❌ Worker DB not found for '{worker_id}' in {SQLITE_DIR}")
        raise FileNotFoundError(f"Worker {worker_id} not found in {SQLITE_DIR}")
    
    # Exécuter query avec gestion d'erreur
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # ✅ Forcer/Capper LIMIT
        q_exec = _cap_limit_in_query(query, cap)
        
        cursor.execute(q_exec)
        rows = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Formatter pour TTS
        summary = _format_for_tts(rows)
        truncated = len(rows) >= cap
        
        return {
            "success": True,
            "rows": rows,
            "count": len(rows),
            "summary": summary,
            "truncated": truncated
        }
    
    except sqlite3.OperationalError as e:
        # Table/colonne manquante → retour gracieux
        logger.warning(f"SQL error for worker {worker_id}: {e}")
        return {
            "success": False,
            "rows": [],
            "count": 0,
            "error": str(e),
            "summary": "Données non disponibles"
        }
    
    except Exception as e:
        # Autres erreurs SQL
        logger.error(f"Query failed for worker {worker_id}: {e}")
        raise


def _validate_query(query: str):
    """
    Valide la requête SQL (whitelist SELECT, blacklist mutations)
    
    Raises:
        ValueError: Si query invalide
    """
    query_upper = query.strip().upper()
    
    # Whitelist: doit commencer par SELECT
    if not query_upper.startswith('SELECT'):
        raise ValueError("Only SELECT queries are allowed")
    
    # Blacklist: mots-clés interdits
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in query_upper:
            raise ValueError(f"Forbidden keyword: {keyword}")


def _format_for_tts(rows: list) -> str:
    """
    Formate résultat SQL pour lecture vocale naturelle
    
    Args:
        rows: Liste de dicts (résultat query)
        
    Returns:
        Texte court et prononçable
    """
    count = len(rows)
    
    if count == 0:
        return "Aucun résultat trouvé."
    
    if count == 1:
        # Une seule ligne
        cols = list(rows[0].keys())
        
        if len(cols) == 1:
            # Une seule colonne = valeur simple
            return f"Résultat : {rows[0][cols[0]]}"
        else:
            # Plusieurs colonnes
            parts = [f"{k} {v}" for k, v in rows[0].items()]
            return "Résultat : " + ", ".join(parts)
    
    if count <= 3:
        # Peu de lignes, lister
        summaries = []
        for i, row in enumerate(rows, 1):
            values = ", ".join([f"{k} {v}" for k, v in row.items()])
            summaries.append(f"Ligne {i} : {values}")
        return f"{count} résultats. " + ". ".join(summaries)
    
    # Beaucoup de lignes, résumer
    first_two = []
    for row in rows[:2]:
        values = ", ".join([str(v) for v in row.values()])
        first_two.append(values)
    
    return f"{count} résultats trouvés. Premiers : {' | '.join(first_two)}"
