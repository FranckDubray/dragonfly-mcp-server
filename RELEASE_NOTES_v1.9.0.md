# 🎉 Release v1.9.0 - YouTube Download Tool

## Highlights

- **Nouveau tool youtube_download** : téléchargement vidéos/audio YouTube
- **Workflow complet transcription** : YouTube → Audio → Whisper
- **Intégration parfaite video_transcribe** : pipeline automatisé
- **Tool count** : 20 tools disponibles (19→20)

## 🆕 YouTube Download Tool

### Features

- **Opérations** :
  - `download` : Télécharge vidéo/audio (MP3 ou MP4)
  - `get_info` : Récupère métadonnées sans télécharger

- **Paramètres flexibles** :
  - `media_type`: **"audio"** (MP3, parfait transcription), "video" (MP4), "both" (séparés)
  - `quality`: "best", "720p", "480p", "360p"
  - `filename`: custom ou auto depuis titre vidéo
  - `max_duration`: 7200s défaut (2h max)
  - `timeout`: 300s défaut (5-600s)

- **Sécurité** :
  - Chroot à `docs/video/`
  - URL validation stricte (YouTube domains uniquement)
  - Filename sanitization (pas de path traversal)
  - Duration limits configurables
  - Timeout enforcement

### Workflow intégré

```bash
# 1. Télécharger audio YouTube (rapide, léger)
youtube_download(url="...", media_type="audio")
# → docs/video/Ma_Video.mp3

# 2. Transcrire avec Whisper (parallèle 3x)
video_transcribe(path="docs/video/Ma_Video.mp3")
# → Transcription complète exploitable !
```

### Use Cases

1. **Conférences tech** → Transcription → Recherche dans contenu
2. **Tutoriels** → Archive texte searchable
3. **Podcasts vidéo** → Extraction citations
4. **Cours en ligne** → Notes automatiques
5. **Interviews** → Analyse de contenu

## 🎬 Test réussi

**Vidéo** : "Le Dîner de cons" - Il s'appelle Juste Leblanc (4min16s)
- ✅ Téléchargement audio : 5.9 MB en quelques secondes
- ✅ Transcription Whisper : ~20 secondes (parallèle 3x)
- ✅ 5 segments avec timestamps
- ✅ Transcription complète exploitable

## 📦 Installation

```bash
git pull origin main
./scripts/dev.sh
```

Le tool `youtube_download` sera automatiquement disponible !

## 📚 Documentation

- [README principal](./README.md) - Vue d'ensemble
- [Tool README](./src/tools/_youtube_download/README.md) - Documentation complète
- [CHANGELOG](./CHANGELOG.md) - Historique détaillé

## 🚀 Breaking Changes

Aucun ! Nouveau tool uniquement.

---

**Full Changelog**: https://github.com/FranckDubray/dragonfly-mcp-server/compare/v1.8.0...v1.9.0
