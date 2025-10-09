#!/usr/bin/env python3
"""Script to commit and push changes"""

import subprocess
import sys

def run_git_command(cmd):
    """Run a git command and return the result"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {cmd}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing: {cmd}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🔍 Checking git status...")
    run_git_command("git status")
    
    print("\n📝 Adding modified files...")
    if not run_git_command("git add src/ui_js.py"):
        sys.exit(1)
    
    print("\n💾 Creating commit...")
    commit_msg = """feat(ui): add alphabetical sorting for tools in control panel

- Sort tools by displayName or name (case-insensitive)
- Improves UX with predictable tool ordering
- Uses localeCompare for natural language sorting"""
    
    if not run_git_command(f'git commit -m "{commit_msg}"'):
        sys.exit(1)
    
    print("\n🚀 Pushing to remote...")
    if not run_git_command("git push"):
        sys.exit(1)
    
    print("\n✅ All done! Changes committed and pushed successfully.")

if __name__ == "__main__":
    main()
