# Changelog

Older entries have been archived under changelogs/ (range-based files).

## 1.6.14 — 2025-01-29

- **Nouveau tool: LLM Agent Multi-turn** (`call_llm_agent`)
  - Orchestration LLM avec enchaînement automatique de tools en séquence
  - Le LLM peut appeler plusieurs tools en séquence, en utilisant les résultats précédents pour décider des prochains appels
  - Architecture multi-tours avec boucle intelligente (jusqu'à 50 itérations configurables)
  - Arrêt naturel basé sur `finish_reason` (standard OpenAI)
  - Exécution parallèle des tools indépendants (asyncio.gather)
  - Gestion d'erreurs intelligente : le LLM peut adapter sa stratégie si un tool échoue
  - Timeout global configurable (défaut: 300s, max: 600s)
  - Cost breakdown détaillé par itération avec usage cumulatif
  - Debug tracking complet de chaque tour (appels LLM, résultats tools, métriques)
  - Prompt system optimisé pour l'orchestration séquentielle
  - Cas d'usage : workflows complexes nécessitant plusieurs étapes dépendantes (recherche juridique Legifrance, analyse multi-sources, navigation dans APIs hiérarchiques, planification de projets)
  - Spécification: `src/tool_specs/call_llm_agent.json` (category: intelligence, tags: llm, agent, orchestration, multi-turn, chain, autonomous)
  - Implémentation: `src/tools/_call_llm_agent/` (core.py, loop.py, executor.py, prompts.py, debug_builder.py, cost_calculator.py, timeout_manager.py)
  - Tests validés avec GPT-5.2 (5 tours séquentiels) et qwen3-next:80b

- **Amélioration: Configuration SSL pour appels LLM**
  - Variable d'environnement `LLM_VERIFY_SSL` pour contrôler la vérification des certificats SSL
  - `true` (défaut): Vérifie les certificats SSL (recommandé pour production)
  - `false`: Désactive la vérification SSL (dev/testing uniquement, supprime les warnings urllib3)
  - Suppression automatique des warnings `InsecureRequestWarning` en mode dev
  - Documentation complète: `docs/SSL_CONFIGURATION.md`
  - Template mis à jour: `.env.example` avec toutes les variables d'environnement documentées

- **Correctifs call_llm_agent**
  - Fix: Boucle infinie quand le LLM retournait `finish_reason="tool_calls"` sans tool_calls (forçage à "stop" si texte présent)
  - Fix: Erreurs de syntaxe Python dans loop.py (ligne 79 et 114)

## 1.6.13 — 2025-01-21

- **Nouveau tool: Client SSH Universel** (`ssh_client`)
  - Client SSH/SFTP pour exécuter des commandes à distance et transférer des fichiers
  - Opérations :
    - `exec` : Exécuter une commande sur le serveur distant (support sudo)
    - `upload` : Envoyer un fichier local vers le serveur (SFTP)
    - `download` : Récupérer un fichier du serveur vers la machine locale (SFTP)
    - `status` : Vérifier la connexion et obtenir des informations système
  - Authentification flexible :
    - Mot de passe (`auth_type: password`)
    - Clé SSH privée (`auth_type: key`) avec support passphrase optionnelle
    - Agent SSH (`auth_type: agent`)
  - Fonctionnalités :
    - Working directory configurablewd`)
    - Variables d'environnement personnalisées (`env`)
    - Timeout configurable (1-600s, défaut: 30s)
    - Vérification de clé d'hôte (strict/auto_add/disabled)
    - Création automatique de répertoires parents (upload)
  - Spécification : `src/tool_specs/ssh_client.json` (category: networking, mote, server, automation)
  - Implémentation : `src/tools/_ssh_client/` (core.py, validators.py, ssh_manager.py, sftp_manager.py)
  - Cas d'usage : Déploiement automatisé, administration serveurs, transferts de fichiers, exécution de scripts distants

- **Nouveau tool: Légifrance LEGI v2** (`legifrance_legi`)
  - Accès aux codes juridiques français (corpus LEGI) avec 3 opérations principales
  - Opérations :
    - `list_codes` : Liste des codes juridiques disponibles (en vigueur/abrogés), filtrable par nature (CODE/ARRETE/DECRET/LOI/ORDONNANCE)
    - `get_code` : Récupère l'arborescence d'un code spécifique (depth 1-10, profondeur configurable)
      - Support des sections racines (filtrage par branche via `root_section_id`)
      - Option `include_articles` pour inclure les IDs d'articles au niveau le plus profond
    - `get_articles` : Récupère le contenu détaillé d'articles (jusqu'à 50 articles par appel)
      - Métadonnées complètes (dates début/fin, nature, état)
      - Liens juridiques (CITATION, MODIFIE, ABROGE, etc.)
      - Fil d'Ariane (breadcrumb) : Code > Livre > Titre > Chapitre > Article
      - Support version historique (paramètre `date`)
  - Architecture :
    - Cache précalculé côté serveur (15 fichiers .json.gz, ~150 MB)
    - 140k+ codes indexés dans SQLite (786 MB)
    - Performances : < 3s pour arborescence complète (depth=5, 1.7M articles)
  - Spécification : `src/tool_specs/legifrance_legi.json` (category: documents, tags: external_sources, knowledge, legal, france)
  - Implémentation : `src/tools/_legifrance_legi/` (api.py, core.py, validators.py, utils.py)
  - Configuration : Variables `.env` (SSH_HOST, CLI_PATH, SSH_KEY_PATH, timeouts)
  - Cas d'usage : Recherche juridique automatisée, analyse de codes, extraction d'articles, workflows agents (call_llm_agent)

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
