#!/bin/bash

# Script to commit and push changes

echo "🔍 Checking git status..."
git status

echo ""
echo "📝 Adding modified files..."
git add src/ui_js.py

echo ""
echo "💾 Creating commit..."
git commit -m "feat(ui): add alphabetical sorting for tools in control panel

- Sort tools by displayName or name (case-insensitive)
- Improves UX with predictable tool ordering
- Uses localeCompare for natural language sorting"

echo ""
echo "🚀 Pushing to remote..."
git push

echo ""
echo "✅ All done! Changes committed and pushed successfully."
