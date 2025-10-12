# 🔄 Reprise de session - Ollama Vision Debug

## 📋 Contexte

Nous travaillons sur le projet **dragonfly-mcp-server** (serveur MCP avec 37 tools).

**Problème actuel** : Le tool `ollama_local` ne gère pas correctement les images pour les modèles de vision (llava:13b).

---

## 🐛 Diagnostic effectué

### Tests réalisés

**Script de test** : `test_gemini_image.sh`  
**Image test** : `docs/gemini_image_68dfaca1489e1.png`

**Résultats** :
- ❌ **TEST 1** (via tool `operation=chat`) : llava dit "je ne vois pas l'image"
- ⏳ **TEST 2** (via tool `operation=generate`) : en attente résultats
- ⏳ **TEST 3** (Ollama direct `/api/generate`) : en attente résultats

### Découverte importante

Via tests curl directs :
- ✅ **`/api/generate`** : fonctionne avec images (llava décrit correctement)
- ❌ **`/api/chat`** : NE supporte PAS les images (llava dit qu'il ne voit pas)

**Source** : Documentation Ollama officielle confirme que seul `/api/generate` supporte les images.

---

## 🔧 Fix appliqué

### Modifications dans `src/tools/_ollama_local/core.py`

**Fonction `handle_chat()`** modifiée pour auto-basculer vers `generate` quand images présentes :

```python
def handle_chat(..., image_files=...):
    # Process images
    images_b64 = _process_images(image_urls, image_files)
    
    # CRITICAL: /api/chat doesn't support images
    # Switch to /api/generate when images present
    if images_b64:
        # Extract last user message as prompt
        prompt = messages[-1]["content"]
        
        # Use generate endpoint instead
        return local_client.generate(
            model=model,
            prompt=prompt,
            images=images_b64,
            ...
        )
    
    # No images: use chat normally
    return local_client.chat(...)
```

**Mais le TEST 1 montre que ça ne marche pas !** La réponse contient `"message": {...}` (format chat), pas `"response": "..."` (format generate).

---

## ❓ Problème actuel

**Le switch vers `generate` ne s'active pas** ou **les images ne sont pas passées correctement**.

**Hypothèses** :
1. `images_b64` est vide (non détecté comme truthy)
2. Le code ne passe pas par le `if images_b64:` 
3. Les images sont skipées quelque part dans `_process_images()`
4. Le tool appelle le mauvais handler

---

## 🎯 Actions nécessaires

### Immédiat
1. Attendre résultats complets des TEST 2 et TEST 3
2. Comparer les 3 sorties pour localiser le bug
3. Ajouter du debug logging dans `handle_chat()` pour voir si le switch est déclenché

### Debug à ajouter
```python
if images_b64:
    print(f"DEBUG: Switching to generate. Images count: {len(images_b64)}")
    print(f"DEBUG: Prompt extracted: {prompt[:100]}...")
```

---

## 📂 Fichiers modifiés (non committés)

- `src/tools/call_llm.py` - Fix chemin images (PROJECT_ROOT)
- `src/tools/_ollama_local/core.py` - Auto-switch vers generate + gestion images
- `src/tools/_ollama_local/services/local_client.py` - Réduction logs streaming
- `src/tool_specs/ollama_local.json` - Ajout paramètres image_files/image_urls
- `CHANGELOG.md` - v1.17.2 documenté

**Script de test actif** : `test_gemini_image.sh`

---

## 📝 Pour reprendre

**Prompt recommandé** :

```
Je reprends le debug du tool ollama_local pour les images de vision (llava).

Fichiers workspace actuels : [liste automatique du workspace]

Situation :
- Test 1 (chat) échoue : llava dit "je ne vois pas l'image" 
- Tests 2 et 3 en attente de résultats
- Le switch auto vers generate ne semble pas fonctionner

Voici les résultats complets du script test_gemini_image.sh :
[coller les 3 résultats]

Analyse et propose un fix.
```

---

## 🔑 Variables d'environnement

```bash
# Partagées entre call_llm et ollama_local
LLM_MAX_IMAGE_FILE_BYTES=5000000  # Max 5 MB par image
LLM_MAX_IMAGE_COUNT=4              # Max 4 images
DOCS_ABS_ROOT=<auto-détecté>      # Racine projet/docs
```

---

## ⚙️ Versions

- **Ollama** : local (localhost:11434)
- **Modèle test** : llava:13b
- **Python** : 3.11+
- **Serveur MCP** : FastAPI (port 8000)

---

**État** : En cours de debug, fix partiellement appliqué mais non fonctionnel. Attente résultats tests 2-3.
