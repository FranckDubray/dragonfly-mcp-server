# Changelog

Older entries have been archived under changelogs/ (range-based files).

## 1.6.13 — 2025-01-21

- **Nouveau tool: Légifrance LEGI** (`legifrance_legi`)
  - Accès au corpus LEGI (codes juridiques français) via SSH.
  - Opérations:
    - `get_summary`: Récupère l'arborescence des codes (en vigueur/abrogés) avec profondeur configurable (depth 1-5).
    - `get_article`: Récupère un ou plusieurs articles avec métadonnées, liens juridiques et fil d'Ariane.
  - Architecture:
    - Client SSH (clé dédiée sans passphrase).
    - Serveur distant: 140k codes indexés dans SQLite (786 MB), cache précalculé pour performances optimales (< 3s pour depth=5).
    - Script CLI Python distant (`legi_cli.py`) avec virtualenv.
  - Spécification: `src/tool_specs/legifrance_legi.json` (category: documents, tags: external_sources, knowledge, legal).
  - Implémentation: `src/tools/_legifrance_legi/` (api.py, core.py, validators.py, utils.py).
  - Configuration: Variables d'environnement `.env` (SSH_HOST, CLI_PATH, timeouts).
  - Performance:
    - Cache précalculé côté serveur (15 fichiers .json.gz, ~150 MB total).
    - Temps de réponse: < 3s pour arborescence complète (depth=5, 1.7M articles).
  - Collaboration: Développé en synergie avec une IA auditeur pour l'infrastructure serveur (indexation, API, précalcul).

## 1.6.12 — 2025-11-07

- Nouveau tool: Voice Chat (voice_chat)
  - Outil unique orchestrant Portal Threads + Whisper + LLM via /execute (aucune nouvelle route HTTP).
  - init_from_portal: récupère le dernier thread via /api/v1/user/threads (+ pagination hydra), reconstruit la fenêtre (alternance user/assistant), limit par défaut 30 (max 100), returned_count et total_items.
  - process_utterance: filtre < 2s (ffprobe), conversion MP3 16 kHz mono si nécessaire, transcription via Whisper, ajout du message user, appel call_llm (max_tokens borné à 50), renvoie transcript/assistant_text/state et tts_text (pour TTS Chrome côté client).
  - Sécurité & chroot: fichiers audio sous docs/audio/tmp, validation des chemins (docs/audio/), pas d'accès hors projet.
  - Conformité guide: spec canonique (additionalProperties:false, category:intelligence), fichiers < 7KB, pas de side-effects à l'import, aucun ajout de dépendance pip (ffmpeg/ffprobe requis côté système).
- LLM_ENDPOINT (Portal): extraction du scheme+host depuis LLM_ENDPOINT (ex: https://ai.dragonflygroup.fr/api/v1/chat/completions → https://ai.dragonflygroup.fr), appels directs à /api/v1/user/threads et /api/v1/user/threads/{id}.
- Validation: test call_llm OK (réponses audio limitées à 50 tokens).

- Généralisation transcription média (audio + vidéo)
  - Remplacement de l'ancien tool video_transcribe par un tool unifié media_transcribe.
  - Spécification: src/tool_specs/media_transcribe.json (category: media, additionalProperties:false, include_segments/segment_limit, model optionnel).
  - Implémentation: extraction audio MP3 16 kHz mono par chunk via FFmpeg (audio_extractor), parallélisation x3 (ThreadPoolExecutor), assemblage full_text; segments optionnels avec counts et indicateur de troncature.
  - Chroot: accepte docs/audio/ et docs/video/; validation stricte.
  - Client Whisper: POST /api/v1/audio/transcriptions (AI_PORTAL_TOKEN + LLM_ENDPOINT), support d'un hint de modèle.
  - Back-compat interne: _voice_chat migre vers le nouveau whisper_client partagé de _media_transcribe.
  - Nettoyage: suppression de src/tools/_video_transcribe/, src/tools/video_transcribe.py et src/tool_specs/video_transcribe.json.

### 1.6.12 – Correctifs et améliorations Voice Chat (post‑release)
- TTS Piper
  - Sélection des modèles: priorité fr_FR > fr_CA > fr, et au sein fr_FR: lessac > siwis > mls.
  - Vitesse par défaut augmentée (length_scale = 0.85) pour un débit plus dynamique.
  - Scripts dev: téléchargement one‑shot des voix FR (lessac, siwis, mls) si models/piper est vide:
    - scripts/download_piper_fr_voices.py (snapshot HuggingFace ciblé)
    - dev.sh/dev.ps1: déclenchent le download une seule fois; fallback vers bootstrap_speech_assets.py si nécessaire.
- Bootstrap HF robuste
  - scripts/bootstrap_speech_assets.py: chemins corrigés + fallback HTTP, écriture atomique.
- Idle timeout
  - Idle pendant TTS: l'inactivité ne déclenche plus pendant que la synthèse parle.
  - Fin de session: renvoie maintenant success:true, ended:true, reason:"idle_timeout" (évite la relance en boucle du tool).
- Rendu de session au client
  - Le résultat inclut la conversation vocale complète (vocal_dialog) limitée à la phase vocale, avec turns/returned_turns.
  - Ajout d'une note explicite pour les LLMs: llm_note="Mode vocal terminé. Reprends en conversation texte.".
- max_tokens
  - Relevé à 100 par défaut (spec + core), pour éviter des réponses tronquées en mode vocal.

Notes
- Ces correctifs n'introduisent pas de nouvelles routes; ils touchent les scripts de dev et le tool voice_chat uniquement.
- Requiert le binaire "piper" dans le PATH pour activer le backend Piper (sinon fallback macOS "say" ou pyttsx3).
