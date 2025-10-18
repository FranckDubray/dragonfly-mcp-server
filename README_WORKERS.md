# Dragonfly MCP — Workers Realtime (Guide d'architecture)

Ce dossier "/workers" fournit une interface temps réel de "workers vocaux" avec:
- un backend FastAPI qui découvre les workers (DB SQLite), construit la config Realtime et proxifie les requêtes,
- un frontend HTML/JS modulaire qui affiche des cartes, lance des appels vocaux, gère l'audio, le WebSocket, les outils et un "process overlay" (time machine) pour visualiser le flux (Mermaid + timeline).

Ce README explique l'architecture et les flux pour qu'un LLM dev puisse travailler sans charger tout le workspace.

---

## TL;DR

- Backend
  - Scanne sqlite3/worker_*.db pour lister les workers.
  - Construit la config Realtime (DB + .env) et démarre une session côté Portal API.
  - Proxifie un outil read-only `worker_query` (SQL SELECT) sécurisé.

- Frontend
  - "Cartes" de workers + bouton "Appeler".
  - Session vocale: sonnerie, WebSocket, micro VAD, tts/stt, VU, outil DB.
  - Process overlay "time machine": Mermaid du process + timeline + replay auto.

- Sécurité/perf
  - SQL read-only, LIMIT forcé/cappé, token redacted, throttling Mermaid (1/s), VAD à 24 kHz, chunks 50 ms.

---

## Fil d'Ariane (où lire quoi)

- Backend endpoints: src/routes/workers.py
- Builder config realtime: src/app_core/workers/config_builder/*
- Scan DB: src/app_core/workers/scanner.py
- Requêtes SQL sécurisées: src/app_core/workers/db_query.py
- Page HTML: src/templates/workers_page.py

- Frontend (groupes):
  - Cartes/grille/statuts: static/js/workers-{cards,grid,status}.js
  - Appel/Audio/VU: workers-{calls,audio,vu,ringback}.js
  - Session (WebSocket+VAD+Tools): workers-session-*.js
  - Process overlay (time machine): workers-process-*.js

---

## Architecture (vue d'ensemble)

```mermaid
flowchart LR
  A[SQLite3 worker_*.db] -->|scan_workers| B(FastAPI /workers)
  B -->|/workers| C[Frontend JS]
  B -->|/workers/{id}/realtime/start| D[Portal API (sessions)]
  D -->|sessionToken+websocketUrl| C
  C -->|WebSocket connect| D
  C -->|input_audio_buffer.append| D
  D -->|output_audio.delta/ transcript/ tool_call| C
  C -->|/workers/{id}/tool/query (SELECT)| B -->|query_worker_db| A

  C -->|openProcess| E[Process Overlay]
  E -->|/workers/{id}/query job_meta/steps| B --> A
  E -->|Mermaid render + Replay| C
```

---

## Backend

### Endpoints clés (src/routes/workers.py)

- GET /workers
  - Retourne la liste des workers découverts (filtrée des champs sensibles).
  - Si Accept: text/html → redirect /workers/ui.
- GET /workers/ui
  - Sert la page HTML (WORKERS_HTML).
- GET /workers/{name}/realtime/config
  - Construit la config Realtime (token masqué) pour inspection.
- POST /workers/{name}/realtime/start
  - Construit le body de session (model, modalities, voice, tools, …).
  - POST vers {api_base}/realtime/sessions (Portal API).
  - Retourne id, websocketUrl, sessionToken, voice, tools, turn_detection, instructions.
- POST /workers/{name}/tool/query
  - Proxy sécurisé pour outil worker_query. Accepte {query, limit}, SELECT uniquement.
  - Appelle query_worker_db (validation + LIMIT cap).
- POST /workers/{name}/query
  - Endpoint legacy pour UI: exécute read-only SELECT.

### Découverte Workers (src/app_core/workers/scanner.py)

- Parcourt sqlite3/worker_*.db.
- Lit job_meta (clé→valeur) pour construire un profil public:
  - id, name, voice, avatar_url, job, employeur, employe_depuis, statut,
  - gallery (gallery_json),
  - enrichissements optionnels: email, bio, tags_json, KPIs, etc.
- Ces infos alimentent les cartes côté frontend.

### Construction Realtime Config (src/app_core/workers/config_builder/*)

- core.py (ou le legacy config_builder.py) orchestre:
  - meta: lecture job_meta + env, normalisation endpoint.
  - tools: charge outils (par défaut worker_query depuis src/tool_specs/worker_query.json), ou “tools_json” dans DB.
  - instructions: base + sections dynamiques:
    - worker_query_prompt (guide tool),
    - dynamic_schema (structure DB),
    - process sections (Mermaid + données process),
  - voice, model, modalities, turn_detection, formats audio.
- Retourne un dict complet utilisé par /realtime/start.

### Requêtes SQL sécurisées (src/app_core/workers/db_query.py)

- Vérifie SELECT-only + blacklist (DROP, DELETE, …).
- Cappe LIMIT (max 200); s’il n’y a pas de LIMIT ajoute LIMIT cap.
- Ouvre la DB en read-only (URI mode=ro).
- Formate un résumé “parlant” pour TTS.
- Gère proprement “OperationalError” (retourne success False + summary neutre).
- Tables typiques exploitées par UI/time-machine:
  - job_meta (skey, svalue),
  - job_state_kv (skey, svalue) — ex: graph mermaid, current_node,
  - job_steps: id, name, status, started_at, finished_at…

---

## Frontend

### Page d’entrée (src/templates/workers_page.py)

- Inclut CSS segmenté et JS modulaire.
- Précharge mermaid (CDN) soft.
- Au DOMContentLoaded:
  - renforce DOM pour anneaux avatar (fallback),
  - collapse galleries by default,
  - init lightbox,
  - loadWorkers().

### Cartes, Grille, Statuts

- workers-grid.js
  - loadWorkers() → GET /workers, rend cartes via renderWorkerCard().
  - Rafraîchit stats & événements (30 s).
- workers-cards.js
  - Rend une carte: avatar + meta + icônes (Process, Galerie) + bouton Appeler.
- workers-status.js
  - refreshWorkerStats(): compte tâches/erreurs, activité 1h.
  - refreshWorkerEvents(): derniers n events depuis job_steps ou fallback job_state_kv.
  - refreshWorkerRuntimeStatus(): running/idle + erreurs récentes (15 min). Poll 5 s.

### Appel vocal (UI) et Audio Sortant

- workers-calls.js
  - callWorker(id): débloque audio, sonnerie (ringback), UX cartes, appelle startRealtimeSession().
  - hangup/endCall: stop session + reset UI.
- workers-ringback.js
  - Génère une sonnerie 440 Hz en PCM16 24 kHz, routée dans audioPlayer (volume indépendant).
- workers-audio.js
  - audioPlayer: PCM16 → WebAudio, queueTime, gain global.
  - setVolume(v), beginDuck/endDuck (ducking pendant barge-in), stopAll immédiat.

### Session vocale — WebSocket, VAD micro, Tools

- workers-session-state.js
  - Définit les globaux de session:
    - ws, sessionId, currentWorkerConfig,
    - verrous: currentResponseId, hasActiveResponse, responseCreatePending,
    - flags: sessionActive, isUserSpeaking, aiSpeaking, gotFirstAIAudio, etc.
    - mini transcripts buffer, timers (call timer).
- workers-session-core.js
  - startRealtimeSession({worker_id}):
    - POST /workers/{id}/realtime/start,
    - connectWebSocket(wsUrl?token=...),
    - envoie system message (conversation.item.create → role system),
    - session.update (instructions + tools),
    - startRecording() (micro),
    - autoGreeting timer (si utilisateur n’a pas encore parlé),
    - call duration chip, ringback stop quand session créée.
  - sendResponseCreateSafe(): protections contre les doublons et throttle.
  - closeSession(): ferme WS, stop enregistrement, stop audio/sonnerie, réinitialise VU/UI.
- workers-session-ws.js
  - connectWebSocket(): ouvre WS, envoie session.update, mappe messages:
    - session.created → stop ringback, system message si manquant,
    - response.created/done/cancelled → met à jour verrous,
    - input_audio_buffer.speech_started/committed → gère isUserSpeaking, barge-in soft,
    - response.output_audio.delta | response.audio.delta → alimente audioPlayer, met à jour VU, aiSpeaking,
    - response.output_audio_transcript.{delta,done} → transcripts (mini),
    - response.function_call_arguments.done → handleFunctionCall(data) (tools).
- workers-session-audio.js
  - Micro capture (AudioWorklet si possible, fallback ScriptProcessor).
  - VAD/Noise-gate simple:
    - Seuils ON/OFF, hysteresis,
    - Fenêtre HOLD ~300 ms avant barge-in effectif (éviter bruit court),
    - Ducking du volume sortie pendant hold, stop audio une fois confirmé,
  - Uplink audio 24 kHz en tranches 50 ms → `input_audio_buffer.append` (base64 PCM16).
- workers-session-tools.js
  - handleFunctionCall() → executeTool():
    - POST /workers/{id}/tool/query (proxy backend SELECT),
    - Reformate le résultat (TS-friendly) et renvoie `function_call_output`,
    - Enchaîne un `response.create` pour que l’IA parle du résultat.

### Affichage VU (anneau avatar)

- workers-vu.js
  - Convertit amplitude PCM16 en RMS [0..1], lisse (EMA), applique classe couleur et set CSS var `--level`.
  - setAISpeaking(on) flag visuel.

---

## Process Overlay “Time Machine”

- workers-process-overlay-core.js
  - Crée l’overlay DOM (dialog), header avec horloge et commandes Replay (⏮ ⏪ ⏹ ⏩ ⏭), zone graph (Mermaid), side panel (timeline + détails).
- workers-process-overlay-events.js
  - openProcess(workerId):
    - ensureMermaid(),
    - Première `refreshProcessView()`,
    - Timer refresh 10 s (tant que overlay ouvert),
    - Bind contrôles replay + clics timeline,
    - Préserve scroll timeline entre refresh.
- workers-process-data.js
  - fetchMermaid(): tente job_state_kv puis job_meta (clés: graph_mermaid, mermaid_graph, process_mermaid, …) -> strip ``` fences.
  - fetchCurrentState(): current_node / current_args depuis job_state_kv.
  - fetchHistory(): job_steps DESC (id, name, status, ts).
  - loadAndShowStepDetails(): affiche une ligne job_steps intégrale.
- workers-process-render.js
  - DFMermaid.renderMermaid(container, source, currentNode):
    - ensure mermaid (CDN fallback),
    - normalize source (répare variantes: “-” → “-->”, quotes, etc.),
    - Ajoute “classDef” et “class” aux 3 nœuds de la “trail” (ex: __hl0/1/2) si WP.hlTrail est défini (ou fallback),
    - Rend en throttlant (min 1/s), attache bridge click (graph → timeline),
    - tryGraphInlineHighlight(trail): sur sélection/interaction, réapplique highlight sans re-render.
- workers-process-ui-core.js
  - refreshProcessView():
    - Récupère Mermaid, current state, history.
    - Construit/reconstruit WP.replaySeq (ordre chronologique, de-dupe nœuds adjacents).
    - Décide le “openNode” (follow tail si WP.atTail).
    - Calcule WP.hlTrail = [node courant, prev1, prev2] avant le render → triple highlight dès le 1er rendu.
    - Appelle renderMermaid(MERMAID_CACHE, graphEl, openNode).
    - Met à jour side panel (timeline), re-surligne la ligne courante.
    - Gère replay: prevReplayLen vs newLen, `wpReplayStart()` pour animer les deltas si on est à la “tail”.
    - KPIs 1h et check de cohérence logs↔graph.
- workers-process-ui-side.js
  - Construit la timeline (Historique) + panneau Détails. Met en cache une signature pour éviter reflow inutile.
- workers-process-ui-highlight.js
  - Sélection timeline par node ou par id (+ trail visuelle -1/-2).
  - Clock (tmClock) depuis ts de l’item.
  - Event `wp-node-select` du graph → lock utilisateur + timeline highlight.
- workers-process-ui-replay.js
  - Gestion du “tape”: `wpReplayStart()/Pause/Stop/StepForward/StepBack/Rewind/ForwardEnd/RenderCurrent`.
  - Avance avec `setInterval` (SPEED_MS ~1200ms).
  - Maintient WP.replayIx, WP.atTail, WP.replayActive + assure highlight trail (3 nœuds) à chaque pas.

---

## Flux complets

### Appel vocal standard

1) Utilisateur clique “Appeler”
   - workers-calls.js: sonnerie (ringback), UX cartes, POST /workers/{id}/realtime/start
2) Backend
   - build_realtime_config → POST Portal API → id, websocketUrl, sessionToken
3) Frontend
   - connectWebSocket(wsUrl?token=...), session.update (instructions + tools)
   - sendSystemMessage(), startRecording() (VAD), autoGreeting si silence
4) Pendant l’appel
   - Micro → VAD → `input_audio_buffer.append` (50ms base64 PCM16)
   - Serveur → `response.output_audio.delta` → audioPlayer + VU
   - Transcripts delta/done → mini transcripts
   - Outil → `response.function_call_arguments.done` → POST /tool/query → `function_call_output` → `response.create`
5) Raccrocher
   - closeSession(): stop WS, VAD, audio, anneaux VU, stop sonnerie.

### Time machine

1) openProcess(workerId)
   - Overlay, ensureMermaid, refreshProcessView
2) refreshProcessView
   - fetchMermaid, fetchHistory, buildReplaySequence
   - WP.hlTrail (3 nœuds) → renderMermaid (class-based highlight)
   - Timeline side, KPIs, cohérence
   - Si atTail et nouveaux steps → anime delta (wpReplayStart)
3) Contrôles
   - ⏮ rewind, ⏪ step back, ⏹ stop (toggle play/stop), ⏩ step fwd, ⏭ end
   - Clic timeline: repositionne WP.replayIx, triple highlight, conserve état play/pause

---

## Extension et points d’attention

- Ajouter un worker
  - Déposer sqlite3/worker_*.db avec tables job_meta/job_steps/job_state_kv.
  - Mettre dans job_meta: worker_name, voice, api_base/llm_endpoint, realtime_model, tools_json (optionnel), gallery_json (optionnel), process_mermaid (graph).
- Ajouter/modifier un tool
  - Par défaut, `worker_query` chargé depuis src/tool_specs/worker_query.json (format type=function).
  - Ou ajouter `tools_json` (liste) dans job_meta (validés par config_builder/tools.py).
- Sécurité SQL
  - Only SELECT + mots-clés interdits + LIMIT cap + mode=ro → risque très limité.
- Audio/VAD
  - Sample rate 24 kHz. HOLD ~300 ms avant barge-in (évite coupe de l’IA sur micro-bruits).
  - Ducking du volume sortie pendant HOLD. Stop du flux sortie à confirmation.
  - input_audio_buffer.append ~50 ms par chunk (1200 samples).
- Mermaid
  - Re-render throttlé (≥ 1/s).
  - Double stratégie de highlight:
    - class-based (injection classDef + class au render),
    - inline (ajout de classes dans le DOM du SVG sans re-render) si source inchangée.
- Polling & timers
  - Cartes: stats/events 30 s
  - Statut runtime: 5 s
  - Process overlay refresh: 10 s
  - Replay: interval SPEED_MS (1200 ms par défaut)

---

## Fichiers et rôles (repères)

Backend:
- src/routes/workers.py — endpoints /workers
- src/app_core/workers/scanner.py — découverte des workers (sqlite3)
- src/app_core/workers/config_builder/* — construction config Realtime (modulaire)
- src/app_core/workers/db_query.py — SELECT sécurisé

Frontend (page):
- src/templates/workers_page.py — HTML de la page UI

Frontend (UI workers):
- static/js/workers-cards.js — rendu d’une carte
- static/js/workers-grid.js — chargement liste + grille
- static/js/workers-status.js — stats/événements/runtime polling
- static/js/workers-gallery.js — galerie + lightbox

Frontend (Appel & Audio):
- static/js/workers-calls.js — démarrer/terminer appel + UX
- static/js/workers-audio.js — player PCM16 + volume + duck
- static/js/workers-vu.js — anneau VU sur avatars
- static/js/workers-ringback.js — sonnerie

Frontend (Session Realtime):
- static/js/workers-session-state.js — globaux session
- static/js/workers-session-core.js — start/stop, system message, response create
- static/js/workers-session-ws.js — WebSocket events (audio/transcripts/tool calls)
- static/js/workers-session-audio.js — micro + VAD + appends
- static/js/workers-session-tools.js — bridge d’outil worker_query

Frontend (Process/Time Machine):
- static/js/workers-process-state.js — globaux WP
- static/js/workers-process-overlay-core.js — DOM overlay
- static/js/workers-process-overlay-events.js — bindings overlay + refresh timer
- static/js/workers-process-data.js — accès DB (graph/history)
- static/js/workers-process-render.js — rendu Mermaid + highlight
- static/js/workers-process-ui-core.js — orchestration refresh + follow-tail
- static/js/workers-process-ui-side.js — timeline + détails
- static/js/workers-process-ui-highlight.js — sélection timeline + horloge
- static/js/workers-process-ui-replay.js — contrôles et autoplay du replay
- static/js/workers-process-consistency.js — cohérence logs ↔ graph

Utilitaires:
- static/js/vad-worklet.js — AudioWorklet pour frames micro
- src/static/js/tools.js, categories.js, config.js, search.js — (autres écrans outils/contrôle hors scope principal workers)

---

## Scénarios “charger minimal”

- Lister et afficher les workers (cartes):
  - Charger: workers-grid.js, workers-cards.js, workers-status.js, workers-gallery.js, routes/workers.py, scanner.py
- Déboguer l’appel vocal (WebSocket, VAD, audio):
  - Charger: workers-calls.js, workers-session-*.js, workers-audio.js, workers-vu.js, workers-ringback.js, routes/workers.py, config_builder/*
- Déboguer le tool worker_query:
  - Charger: workers-session-tools.js, routes/workers.py (tool/query), db_query.py
- Time machine (Mermaid + timeline + replay):
  - Charger: workers-process-*.js, db_query.py, routes/workers.py, (optionnel) config_builder.process_* si vous modifiez la génération du prompt process

---

## Conventions et globals à connaître

- Session (workers-session-state.js):
  - ws, sessionId, currentWorkerConfig, sessionActive
  - currentResponseId, hasActiveResponse, responseCreatePending
  - window.isUserSpeaking, window.aiSpeaking
  - timers: callTimer; mini transcripts DOM
- Process overlay (workers-process-state.js):
  - WP: { replayTimer, replayActive, replayIx, replaySeq, replayMeta, processWorkerId, kpisSig, timelineSig, mermaidReady, hlTrail, atTail, prevReplayLen, _initDone, userLockExpires }
- VU:
  - updateVu(workerId, amp), resetVu(workerId), setAISpeaking(on)
  - ampFromPcm16Base64(b64)
- Mermaid:
  - DFMermaid.renderMermaid(container, source, currentNode)
  - tryGraphInlineHighlight(trail)
  - WP.hlTrail = [cur, -1, -2] → triple highlight class-based au render + inline ensuite

---

## Performance, Sécurité, Robustesse

- Mermaid throttling 1/s pour éviter reflow excessif.
- “Inline highlight” pour les changements de sélection sans re-render.
- SQL: Only SELECT + blacklist + LIMIT cap + mode=ro → risque très limité.
- VAD HOLD window + ducking: évite les barge-in intempestifs.
- Ringback: simple générateur sinus PCM, non bloquant, volume indépendant.

---

## Dépannage rapide

- “Aucun worker”:
  - sqlite3/ manquant? Noms de fichiers worker_*.db?
  - job_meta lisible?
- Démarrage session échoue:
  - LLM_ENDPOINT/AI_PORTAL_TOKEN/REALTIME_MODEL définis?
  - Portal renvoie websocketUrl + sessionToken?
- Pas d’audio IA:
  - Check response.output_audio.delta reçu?
  - workers-audio.js context s’ouvre bien (unlock)?
- Time machine figée:
  - WP.replayStart/Active/Timer? Pas de pause forcée au clic?
  - WP.hlTrail calculée avant le premier render?

---

## Licence et contacts

- Logs et URL internes masquées ici; adaptez à votre environnement.
- Pour contributions (patches), concentrez-vous sur les modules décrits dans “Scénarios charger minimal”.
- Pour toute question d’intégration/exploitation: se référer aux auteurs du projet Dragonfly MCP.
