# Tests Workers Realtime - Validation Post-Audit

## Objectif
Valider que le flow Portal AI fonctionne correctement après corrections.

## Prérequis
- [ ] `.env` configuré avec `AI_PORTAL_URL` et `AI_PORTAL_TOKEN`
- [ ] Worker DB existant (`sqlite3/worker_alain.db` ou autre)
- [ ] Serveur MCP lancé (`./scripts/dev.sh`)

## Tests fonctionnels

### 1. Backend - Configuration worker
```bash
# Test 1 : Vérifier scan workers
curl http://localhost:8000/workers

# Attendu : 
{
  "workers": [
    {
      "id": "alain",
      "name": "Alain",
      "voice": "ash",
      "has_persona": true,
      ...
    }
  ],
  "count": 1
}
```

```bash
# Test 2 : Récupérer config Realtime
curl http://localhost:8000/workers/alain/realtime/config

# Attendu :
{
  "worker_id": "alain",
  "worker_name": "Alain",
  "api_base": "https://ai.dragonflygroup.fr/api/v1",
  "token": "tok_...",
  "model": "gpt-4o-mini-realtime-preview-2024-12-17",
  "instructions": "...",
  "tools": [{...}],
  "voice": "ash",
  "turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 800,
    "interrupt_response": true
  },
  "input_audio_format": "pcm16",
  "output_audio_format": "pcm16"
}
```

**Validation** :
- ✅ `api_base` pointe vers Portal (pas OpenAI direct)
- ✅ `turn_detection.type` = `server_vad`
- ✅ `tools` contient `sqlite_db` avec instruction worker DB

---

### 2. Frontend - Session creation

**Test navigateur** (Chrome/Firefox) :
1. Ouvrir `http://localhost:8000/workers/ui`
2. Cliquer sur card worker "Alain"
3. Observer la console navigateur :

```javascript
// Attendu dans la console :
🔧 Creating session: https://ai.dragonflygroup.fr/api/v1/realtime/sessions
✅ Session created: sess_abc123
✅ WebSocket connected
🔧 Server VAD enabled
✅ Microphone granted
```

**Validation** :
- ✅ POST `/realtime/sessions` réussit (status 200)
- ✅ WebSocket connecté (status `Connecté` en vert)
- ✅ Micro actif (badge vert)

---

### 3. Audio pipeline - Parler avec le worker

**Test vocal** :
1. Cliquer sur bouton 🎙️ "Parler"
2. Dire "Salut Alain, combien de mails tu as traité aujourd'hui ?"
3. Arrêter enregistrement (bouton 🛑)
4. Observer la transcription

**Attendu** :
```
[Vous]
Salut Alain, combien de mails tu as traité aujourd'hui ?

[Assistant]
Bonjour ! J'ai traité 47 mails depuis ce matin. Dont 3 spams.
```

**Console attendue** :
```javascript
🎙️ Recording started
TX audio chunk 4800 bytes
TX audio chunk 4800 bytes
...
[Recording] commit + response.create
🎙️ Recording stopped
[Latency] 342ms
```

**Validation** :
- ✅ Audio envoyé en chunks PCM16
- ✅ Transcription utilisateur apparaît
- ✅ Réponse assistant jouée (audio + texte)
- ✅ Latency < 1000ms

---

### 4. Server VAD - Interruption

**Test interruption** :
1. Démarrer enregistrement
2. Dire "Alain, raconte-moi..." (pause naturelle)
3. **Pendant que l'assistant parle**, dire "Stop, c'est bon merci"

**Attendu** :
- ✅ L'assistant s'arrête immédiatement (server_vad détecte l'interruption)
- ✅ Nouvelle réponse courte de l'assistant

**Console** :
```javascript
[Recording] response.cancel sent
response.audio.delta stopped
```

**Validation** :
- ✅ `turn_detection.interrupt_response: true` fonctionne
- ✅ Pas de VAD client (server-side uniquement)

---

### 5. Tool calling - Query SQLite

**Test requête DB** :
1. Dire "Alain, montre-moi mes 3 derniers mails classés"
2. Observer l'indicateur outil (spinner jaune en bas)

**Console attendue** :
```javascript
[Tool] Args delta buffered: {callId: "call_xyz", size: 127}
[Tool] Executing: {callId: "call_xyz", name: "sqlite_db", args: {...}}
POST /execute (sqlite_db)
[Tool] Output sent: {callId: "call_xyz", length: 234}
```

**Validation** :
- ✅ Indicateur outil visible pendant l'exécution
- ✅ Requête SQL exécutée avec `db="worker_alain"`
- ✅ Résultat formaté pour TTS (court et prononçable)

---

## Tests non-régression

### 1. Worker sans DB
```bash
curl http://localhost:8000/workers/worker_inexistant/realtime/config

# Attendu : HTTP 404
{
  "detail": "Worker worker_inexistant not found in ..."
}
```

### 2. .env manquant
```bash
# Supprimer temporairement AI_PORTAL_URL de .env
curl http://localhost:8000/workers/alain/realtime/config

# Attendu : HTTP 500
{
  "detail": "Internal error: AI_PORTAL_URL not configured in .env"
}
```

### 3. Multi-workers
```bash
# Si plusieurs workers (alain, sophie, etc.)
curl http://localhost:8000/workers

# Attendu : Liste complète
{
  "workers": [
    {"id": "alain", ...},
    {"id": "sophie", ...}
  ],
  "count": 2
}
```

---

## Checklist finale

- [ ] **Backend** : Config retourne Portal URL (pas OpenAI direct)
- [ ] **Backend** : `turn_detection` avec server_vad configuré
- [ ] **Frontend** : Session creation en 2 étapes (POST + WebSocket)
- [ ] **Frontend** : Audio PCM16 24kHz envoyé correctement
- [ ] **Frontend** : Transcriptions affichées (user + assistant)
- [ ] **Server VAD** : Interruption fonctionne (parler pendant réponse)
- [ ] **Tools** : sqlite_db exécuté avec bonne DB worker
- [ ] **Latency** : < 1000ms première réponse
- [ ] **Audio** : Lecture fluide (pas de coupures)
- [ ] **Errors** : Gestion propre (pas de crash serveur)

---

## Métriques attendues

| Métrique | Valeur cible | Valeur mesurée |
|----------|--------------|----------------|
| Session creation | < 2s | _____ |
| First response latency | < 1000ms | _____ |
| Audio chunk rate | ~8-10/sec | _____ |
| Tool execution | < 500ms | _____ |
| Interruption response | < 200ms | _____ |

---

## Conclusion

**Status** : ☐ PASS ☐ FAIL

**Notes** :
_____________________________________________
_____________________________________________
_____________________________________________
