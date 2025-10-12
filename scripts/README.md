# Scripts Directory

Ce répertoire contient des scripts bash qui peuvent être exécutés sur des serveurs distants via le tool `ssh_admin`.

## 🎯 Usage avec ssh_admin

### Exécuter un script local sur serveur distant

```python
# Script simple (sans arguments)
ssh_admin(
    operation="exec_file",
    profile="prod",
    script_path="scripts/example_ssh_health_check.sh"
)

# Script avec arguments
ssh_admin(
    operation="exec_file",
    profile="prod",
    script_path="scripts/example_ssh_service_check.sh",
    args=["nginx", "postgresql", "docker"]
)
```

## 📋 Scripts d'exemple

### `example_ssh_health_check.sh`
Check santé système complet :
- CPU load
- Memory usage
- Disk usage
- Network interfaces

### `example_ssh_service_check.sh`
Vérifie le statut de services systemd :
- Accepte une liste de services en arguments
- Affiche statut + uptime
- Exit code 0 si tous OK

## ✍️ Créer vos propres scripts

### Best practices

```bash
#!/bin/bash
# Description de votre script

# Stop on error
set -e

# Gérer les arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <arg1> [arg2]"
    exit 1
fi

# Votre logique ici
echo "Running with args: $@"

# Variables d'arguments
ARG1="$1"
ARG2="${2:-default_value}"

# Sortie structurée pour parsing
echo "RESULT: success"
```

### Sécurité

- ✅ Toujours utiliser `set -e` pour arrêter sur erreur
- ✅ Valider les arguments
- ✅ Échapper les variables avec quotes : `"$var"`
- ✅ Tester localement avant déploiement
- ⚠️ Éviter `rm -rf` sans validation
- ⚠️ Pas de credentials hardcodés

### Organisation

```
scripts/
├── deployment/
│   ├── deploy_nginx.sh
│   └── rollback_nginx.sh
├── monitoring/
│   ├── check_disk.sh
│   └── check_services.sh
├── maintenance/
│   ├── cleanup_logs.sh
│   └── rotate_backups.sh
└── README.md
```

## 🔧 Debug

Si un script échoue :

```python
# Vérifier exit code
result = ssh_admin(operation="exec_file", profile="prod", script_path="scripts/test.sh")
print(f"Exit code: {result['exit_code']}")
print(f"Stderr: {result['stderr']}")

# Tester localement d'abord
ssh_admin(operation="exec", profile="prod", command="bash -x /path/to/script.sh")
```

## 📚 Ressources

- [Bash Best Practices](https://mywiki.wooledge.org/BashGuide/Practices)
- [ShellCheck](https://www.shellcheck.net/) - Linter bash
- Systemd: `man systemctl`
