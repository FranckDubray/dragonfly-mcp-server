#!/bin/bash
# Script pour créer la release v1.9.0 sur GitHub
# Usage: ./scripts/create_release_v1.9.0.sh

set -e

echo "🚀 Création de la release v1.9.0..."

# Vérifier que le token GitHub est configuré
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ Erreur: GITHUB_TOKEN non configuré dans .env"
    echo "Veuillez générer un nouveau token sur:"
    echo "https://github.com/settings/tokens/new"
    echo "Avec le scope 'repo' complet"
    exit 1
fi

# Charger les notes de release
RELEASE_BODY=$(cat RELEASE_NOTES_v1.9.0.md)

# Créer la release via l'API GitHub
echo "📝 Création de la release..."
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/FranckDubray/dragonfly-mcp-server/releases \
  -d @- << EOF
{
  "tag_name": "v1.9.0",
  "target_commitish": "main",
  "name": "v1.9.0 - YouTube Download Tool",
  "body": $(echo "$RELEASE_BODY" | jq -Rs .),
  "draft": false,
  "prerelease": false
}
EOF

echo ""
echo "✅ Release créée avec succès!"
echo "🔗 https://github.com/FranckDubray/dragonfly-mcp-server/releases/tag/v1.9.0"
