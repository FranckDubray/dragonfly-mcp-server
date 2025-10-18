import logging
from datetime import datetime, timezone
logger = logging.getLogger(__name__)

def build_base_instructions(worker_id: str, meta: dict) -> str:
    worker_name = meta.get('worker_name', worker_id.capitalize()).strip()
    persona = (meta.get('persona') or f"Je suis {worker_name}.").strip()
    job = (meta.get('job') or '').strip()
    employeur = (meta.get('employeur') or '').strip()
    employe_depuis = (meta.get('employe_depuis') or '').strip()
    client_info = meta.get('client_info')

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A %d %B %Y")
    time_str = now.strftime("%H:%M")
    for en, fr in {'Monday':'Lundi','Tuesday':'Mardi','Wednesday':'Mercredi','Thursday':'Jeudi','Friday':'Vendredi','Saturday':'Samedi','Sunday':'Dimanche'}.items():
        date_str = date_str.replace(en, fr)
    for en, fr in {'January':'Janvier','February':'Février','March':'Mars','April':'Avril','May':'Mai','June':'Juin','July':'Juillet','August':'Août','September':'Septembre','October':'Octobre','November':'Novembre','December':'Décembre'}.items():
        date_str = date_str.replace(en, fr)

    identite_section = f"""IDENTITÉ DU WORKER
Tu t'appelles {worker_name}.
{('Métier : ' + job + '\n') if job else ''}{('Employeur : ' + employeur + (' (depuis ' + employe_depuis + ')') if employe_depuis else '') + '\n' if employeur else ''}
"""

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
