# VS Code Control Tool - Documentation

## Vue d'ensemble

L'outil **VS Code Control** permet de contrôler VS Code en local via son interface CLI (`code`). Il offre des fonctionnalités pour ouvrir des fichiers/dossiers, gérer les extensions, modifier les paramètres, et explorer les workspaces.

## Architecture

```
src/tools/vscode_control.py              # Point d'entrée principal
src/tool_specs/vscode_control.json       # Spécification MCP
src/tools/_vscode_control/
  ├── __init__.py                        # Module init
  ├── cli_ops.py                         # Opérations CLI (code command)
  ├── settings_ops.py                    # Gestion des paramètres
  ├── workspace_ops.py                   # Opérations workspace
  └── README.md                          # Cette documentation
```

## Opérations disponibles

### 📁 Fichiers et Dossiers

#### `open_file`
Ouvre un fichier dans VS Code.

```json
{
  "operation": "open_file",
  "file_path": "src/main.py",
  "line_number": 42,
  "column_number": 10,
  "new_window": false,
  "wait": false
}
```

#### `open_folder`
Ouvre un dossier dans VS Code.

```json
{
  "operation": "open_folder",
  "folder_path": "/path/to/project",
  "new_window": false,
  "add_to_workspace": false
}
```

#### `diff_files`
Compare deux fichiers côte à côte.

```json
{
  "operation": "diff_files",
  "file_path_1": "version1.txt",
  "file_path_2": "version2.txt",
  "wait": false
}
```

#### `goto_line`
Ouvre un fichier à une ligne spécifique.

```json
{
  "operation": "goto_line",
  "file_path": "src/app.py",
  "line_number": 100,
  "column_number": 5
}
```

### 🔌 Extensions

#### `list_extensions`
Liste toutes les extensions installées.

```json
{
  "operation": "list_extensions",
  "show_categories": false,
  "include_disabled": false
}
```

**Réponse:**
```json
{
  "success": true,
  "extensions": [
    "ms-python.python",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode"
  ],
  "count": 3,
  "message": "Found 3 extension(s)"
}
```

#### `install_extension`
Installe une extension.

```json
{
  "operation": "install_extension",
  "extension_id": "ms-python.python"
}
```

#### `uninstall_extension`
Désinstalle une extension.

```json
{
  "operation": "uninstall_extension",
  "extension_id": "ms-python.python"
}
```

### ⚙️ Paramètres

#### `get_settings`
Récupère les paramètres VS Code.

```json
{
  "operation": "get_settings",
  "scope": "user",
  "setting_key": "editor.fontSize"
}
```

**Réponse:**
```json
{
  "success": true,
  "scope": "user",
  "setting": {
    "editor.fontSize": 14
  },
  "message": "Setting 'editor.fontSize' retrieved"
}
```

Pour récupérer tous les paramètres, omettez `setting_key`:

```json
{
  "operation": "get_settings",
  "scope": "user"
}
```

#### `update_settings`
Modifie un paramètre VS Code.

```json
{
  "operation": "update_settings",
  "setting_key": "editor.fontSize",
  "setting_value": 16,
  "scope": "user"
}
```

**Types de valeurs supportés:**
- String: `"Monaco"`
- Number: `14`
- Boolean: `true`
- Object: `{"enabled": true, "delay": 500}`

#### `list_common_settings`
Liste les paramètres les plus courants avec descriptions.

```json
{
  "operation": "list_common_settings"
}
```

### 🗂️ Workspace

#### `get_workspace_info`
Récupère les informations sur le workspace actuel.

```json
{
  "operation": "get_workspace_info"
}
```

**Réponse:**
```json
{
  "success": true,
  "current_directory": "/path/to/project",
  "has_vscode_folder": true,
  "workspace_files": ["project.code-workspace"],
  "vscode_files": ["settings.json", "launch.json"],
  "message": "Workspace info for: project"
}
```

#### `search_files`
Recherche des fichiers selon un pattern glob.

```json
{
  "operation": "search_files",
  "search_pattern": "*.py",
  "search_path": "/path/to/search"
}
```

**Réponse:**
```json
{
  "success": true,
  "pattern": "*.py",
  "matches": [
    {
      "path": "/full/path/to/file.py",
      "name": "file.py",
      "size": 1024,
      "relative_path": "src/file.py"
    }
  ],
  "count": 1,
  "message": "Found 1 file(s) matching '*.py'"
}
```

#### `get_project_structure`
Récupère la structure du projet sous forme d'arbre.

```json
{
  "operation": "get_project_structure",
  "max_depth": 3,
  "include_hidden": false
}
```

### 🔧 Utilitaires

#### `get_version`
Récupère la version de VS Code.

```json
{
  "operation": "get_version"
}
```

#### `get_status`
Récupère le statut de VS Code.

```json
{
  "operation": "get_status"
}
```

## Exemples d'utilisation

### Exemple 1: Ouvrir un fichier à une ligne spécifique

```python
# Via l'API MCP
result = mcp_client.call_tool("vscode_control", {
    "operation": "open_file",
    "file_path": "src/main.py",
    "line_number": 42
})
```

### Exemple 2: Installer plusieurs extensions

```python
extensions = [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-toolsai.jupyter"
]

for ext in extensions:
    result = mcp_client.call_tool("vscode_control", {
        "operation": "install_extension",
        "extension_id": ext
    })
    print(f"Installed: {ext}")
```

### Exemple 3: Configurer l'éditeur

```python
settings = {
    "editor.fontSize": 14,
    "editor.tabSize": 4,
    "editor.formatOnSave": True,
    "files.autoSave": "afterDelay"
}

for key, value in settings.items():
    result = mcp_client.call_tool("vscode_control", {
        "operation": "update_settings",
        "setting_key": key,
        "setting_value": value,
        "scope": "user"
    })
```

### Exemple 4: Rechercher tous les fichiers Python

```python
result = mcp_client.call_tool("vscode_control", {
    "operation": "search_files",
    "search_pattern": "*.py"
})

for file in result["matches"]:
    print(f"Found: {file['relative_path']} ({file['size']} bytes)")
```

## Limitations actuelles

Certaines opérations nécessitent une extension VS Code pour fonctionner pleinement:

- ❌ `execute_command` - Exécuter des commandes VS Code arbitraires
- ❌ `create_terminal` - Créer un terminal intégré
- ❌ `run_in_terminal` - Exécuter des commandes dans le terminal
- ❌ `reload_window` - Recharger la fenêtre VS Code
- ❌ `list_open_files` - Lister les fichiers actuellement ouverts
- ❌ `close_file` - Fermer un fichier spécifique

Ces opérations retournent un message indiquant qu'une extension est nécessaire.

## Extension future (optionnelle)

Pour débloquer les fonctionnalités avancées, vous pouvez créer une extension VS Code qui expose une API REST locale. Cette extension permettrait:

1. Exécution de commandes VS Code arbitraires
2. Contrôle des terminaux intégrés
3. Gestion des fichiers ouverts
4. Accès à l'état de l'éditeur en temps réel

## Prérequis

- VS Code installé
- CLI `code` disponible dans le PATH
- Python 3.8+

## Installation

L'outil est automatiquement découvert par le serveur MCP au démarrage. Aucune installation supplémentaire n'est nécessaire.

## Dépannage

### Erreur: "VS Code CLI 'code' not found"

**Solution:** Assurez-vous que VS Code est installé et que la commande `code` est dans votre PATH.

**Windows:**
```cmd
# Ajouter VS Code au PATH
set PATH=%PATH%;C:\Program Files\Microsoft VS Code\bin
```

**macOS/Linux:**
```bash
# Ouvrir VS Code et utiliser la palette de commandes (Cmd+Shift+P)
# Chercher: "Shell Command: Install 'code' command in PATH"
```

### Les paramètres ne sont pas sauvegardés

Vérifiez que vous avez les permissions d'écriture sur:
- Windows: `%APPDATA%\Code\User\settings.json`
- macOS: `~/Library/Application Support/Code/User/settings.json`
- Linux: `~/.config/Code/User/settings.json`

## Support

Pour toute question ou problème, consultez la documentation principale du projet Dragonfly MCP Server.
