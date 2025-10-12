#!/bin/bash
# Commit and push fix for v1.17.2

set -e

echo "🔧 Adding modified files to git..."
git add CHANGELOG.md src/tools/call_llm.py src/tools/_ollama_local/services/local_client.py

echo "📝 Creating commit..."
git commit -m "fix(tools): critical fixes for call_llm images and ollama streaming

- call_llm: fix image path resolution with dynamic project root detection
- ollama_local: fix massive log flooding (98-99.6% output reduction)
- Both fixes comply with LLM_DEV_GUIDE output size policies

Release: v1.17.2"

echo "🚀 Pushing to origin..."
git push origin main

echo "✅ Done! Changes pushed to main branch."
echo ""
echo "📦 To create a release:"
echo "   gh release create v1.17.2 --title \"v1.17.2 - Critical Fixes\" --notes \"See CHANGELOG.md for details\""
