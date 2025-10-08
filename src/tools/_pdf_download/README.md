# PDF Download Tool

Télécharge des fichiers PDF depuis des URLs et les sauvegarde dans `docs/pdfs`.

## 🎯 Fonctionnalités

- ✅ Téléchargement HTTP/HTTPS avec timeout configurable
- ✅ Validation PDF (magic bytes `%PDF-`)
- ✅ Gestion automatique des noms uniques (suffixes `_1`, `_2`, etc.)
- ✅ Option d'écrasement (`overwrite`)
- ✅ Chroot sécurisé dans `docs/pdfs`
- ✅ Extraction automatique du nom depuis l'URL
- ✅ Support User-Agent personnalisé
- ✅ Gestion des redirections

## 📋 Paramètres

| Paramètre | Type | Requis | Défaut | Description |
|-----------|------|--------|--------|-------------|
| `operation` | string | ✅ | - | Opération (`"download"`) |
| `url` | string | ✅ | - | URL complète du PDF (http/https) |
| `filename` | string | ❌ | extrait de l'URL | Nom de fichier personnalisé (`.pdf` ajouté auto) |
| `overwrite` | boolean | ❌ | `false` | Si `true`, écrase le fichier existant |
| `timeout` | integer | ❌ | `60` | Timeout en secondes (5-300) |

## 🚀 Exemples d'utilisation

### Téléchargement simple

```json
{
  "tool": "pdf_download",
  "params": {
    "operation": "download",
    "url": "https://arxiv.org/pdf/2301.00001.pdf"
  }
}
```

**Résultat :**
- Fichier sauvegardé : `docs/pdfs/2301.00001.pdf`
- Si existe déjà : `docs/pdfs/2301.00001_1.pdf`

### Nom personnalisé

```json
{
  "tool": "pdf_download",
  "params": {
    "operation": "download",
    "url": "https://example.com/paper.pdf",
    "filename": "research_llm_2025"
  }
}
```

**Résultat :** `docs/pdfs/research_llm_2025.pdf`

### Écrasement

```json
{
  "tool": "pdf_download",
  "params": {
    "operation": "download",
    "url": "https://example.com/report.pdf",
    "filename": "monthly_report.pdf",
    "overwrite": true
  }
}
```

**Résultat :** Écrase `docs/pdfs/monthly_report.pdf` s'il existe

### Timeout long

```json
{
  "tool": "pdf_download",
  "params": {
    "operation": "download",
    "url": "https://example.com/large-document.pdf",
    "timeout": 180
  }
}
```

## 📤 Format de réponse

### Succès

```json
{
  "success": true,
  "message": "PDF downloaded successfully",
  "file": {
    "path": "docs/pdfs/paper.pdf",
    "absolute_path": "/path/to/project/docs/pdfs/paper.pdf",
    "filename": "paper.pdf",
    "size_bytes": 2457600,
    "size_mb": 2.34,
    "content_type": "application/pdf"
  },
  "source": {
    "url": "https://example.com/paper.pdf",
    "timeout_used": 60
  },
  "overwritten": false
}
```

### Erreur

```json
{
  "error": "HTTP error 404: Not Found"
}
```

```json
{
  "error": "Downloaded file is not a valid PDF (magic bytes check failed)"
}
```

## 🔒 Sécurité

### Validation des entrées
- URL : protocole `http`/`https` uniquement
- Filename : caractères alphanumériques, espaces, `.`, `-`, `_` uniquement
- Pas de path traversal (`/`, `\`, `..`)

### Chroot
- Tous les fichiers sauvegardés dans `docs/pdfs`
- Pas d'accès en dehors de ce répertoire

### Validation PDF
- Vérification magic bytes (`%PDF-`)
- Protection contre les faux PDFs

## 🧩 Architecture

```
src/tools/pdf_download/
  __init__.py              # Thin glue (run + spec)
  api.py                   # Routing
  core.py                  # Logique métier
  validators.py            # Validation inputs
  utils.py                 # Helpers (noms uniques, paths)
  services/
    downloader.py          # HTTP download isolé
  README.md                # Cette doc
```

## 🛠️ Intégration avec autres tools

### Chaîne complète de traitement PDF

```python
# 1. Télécharger
{
  "tool": "pdf_download",
  "params": {
    "operation": "download",
    "url": "https://arxiv.org/pdf/2301.00001.pdf",
    "filename": "llm_paper"
  }
}
# → docs/pdfs/llm_paper.pdf

# 2. Extraire le texte
{
  "tool": "pdf2text",
  "params": {
    "path": "docs/pdfs/llm_paper.pdf"
  }
}

# 3. Rechercher dans le PDF
{
  "tool": "pdf_search",
  "params": {
    "path": "docs/pdfs/llm_paper.pdf",
    "query": "transformer architecture"
  }
}
```

## ⚠️ Limitations

- Taille max : dépend de la mémoire disponible (streaming non implémenté)
- Formats : PDF uniquement (pas de conversion automatique)
- Authentification : pas de support authentification HTTP (Basic/Bearer)
- Proxy : pas de support proxy

## 🐛 Dépannage

### Erreur "Download timeout"
- Augmenter `timeout` (max 300s)
- Vérifier la taille du fichier

### Erreur "Not a valid PDF"
- L'URL pointe vers une page HTML (pas un PDF direct)
- Le serveur renvoie du contenu corrompu
- Vérifier l'URL dans un navigateur

### Erreur "Permission denied"
- Vérifier les permissions du dossier `docs/pdfs`
- Sur Unix : `chmod 755 docs/pdfs`

## 📝 TODO (futures améliorations)

- [ ] Support authentification HTTP (Basic, Bearer)
- [ ] Streaming pour très gros fichiers
- [ ] Support proxy
- [ ] Métadonnées PDF (auteur, titre, date)
- [ ] Téléchargement batch (liste d'URLs)
- [ ] Cache (éviter re-télécharger si hash identique)
