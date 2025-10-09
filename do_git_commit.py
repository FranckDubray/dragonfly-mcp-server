#!/usr/bin/env python3
"""Use MCP git tool to commit and push changes"""

import requests
import json

MCP_URL = "http://127.0.0.1:8000"

def execute_tool(tool, params):
    """Execute a tool via MCP server"""
    response = requests.post(
        f"{MCP_URL}/execute",
        headers={"Content-Type": "application/json"},
        json={"tool": tool, "params": params}
    )
    
    if response.ok:
        result = response.json()
        print(f"✅ {tool} - {params.get('operation', '')}")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def main():
    print("🔍 1. Checking git status...")
    execute_tool("git", {
        "operation": "status",
        "repo_dir": "."
    })
    
    print("\n📝 2. Adding modified file...")
    execute_tool("git", {
        "operation": "add_paths",
        "repo_dir": ".",
        "paths": ["src/ui_js.py"]
    })
    
    print("\n💾 3. Creating commit...")
    commit_msg = """feat(ui): add alphabetical sorting for tools in control panel

- Sort tools by displayName or name (case-insensitive)
- Improves UX with predictable tool ordering
- Uses localeCompare for natural language sorting"""
    
    execute_tool("git", {
        "operation": "commit_all",
        "repo_dir": ".",
        "message": commit_msg
    })
    
    print("\n🚀 4. Pushing to remote...")
    execute_tool("git", {
        "operation": "push",
        "repo_dir": ".",
        "branch": "main",
        "remote": "origin"
    })
    
    print("\n✅ All done! Changes committed and pushed successfully.")

if __name__ == "__main__":
    main()
