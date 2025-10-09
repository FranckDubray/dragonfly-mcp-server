#!/bin/bash

MCP_URL="http://127.0.0.1:8000"

echo "🔍 1. Checking git status..."
curl -s -X POST "$MCP_URL/execute" \
  -H 'Content-Type: application/json' \
  -d '{"tool":"git","params":{"operation":"status","repo_dir":"."}}' | jq '.'

echo ""
echo "📝 2. Adding modified file..."
curl -s -X POST "$MCP_URL/execute" \
  -H 'Content-Type: application/json' \
  -d '{"tool":"git","params":{"operation":"add_paths","repo_dir":".","paths":["src/ui_js.py"]}}' | jq '.'

echo ""
echo "💾 3. Creating commit..."
curl -s -X POST "$MCP_URL/execute" \
  -H 'Content-Type: application/json' \
  -d '{
    "tool":"git",
    "params":{
      "operation":"commit_all",
      "repo_dir":".",
      "message":"feat(ui): add alphabetical sorting for tools in control panel\n\n- Sort tools by displayName or name (case-insensitive)\n- Improves UX with predictable tool ordering\n- Uses localeCompare for natural language sorting"
    }
  }' | jq '.'

echo ""
echo "🚀 4. Pushing to remote..."
curl -s -X POST "$MCP_URL/execute" \
  -H 'Content-Type: application/json' \
  -d '{"tool":"git","params":{"operation":"push","repo_dir":".","branch":"main","remote":"origin"}}' | jq '.'

echo ""
echo "✅ All done! Changes committed and pushed successfully."
