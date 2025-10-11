#!/usr/bin/env python3
"""Script pour ajouter le champ 'category' à tous les tool_specs JSON."""

import json
from pathlib import Path

# Mapping tool_name -> category
CATEGORIES = {
    # Intelligence & Orchestration
    "call_llm": "intelligence",
    "ollama_local": "intelligence",
    "academic_research_super": "intelligence",
    
    # Development
    "git": "development",
    "gitbook": "development",
    
    # Communication
    "email_send": "communication",
    "imap": "communication",
    "discord_webhook": "communication",
    
    # Data & Storage
    "sqlite_db": "data",
    "excel_to_sqlite": "data",
    "script_executor": "data",
    
    # Documents
    "pdf_download": "documents",
    "pdf_search": "documents",
    "pdf2text": "documents",
    "office_to_pdf": "documents",
    "universal_doc_scraper": "documents",
    
    # Media
    "youtube_search": "media",
    "youtube_download": "media",
    "video_transcribe": "media",
    "ffmpeg_frames": "media",
    
    # Transportation
    "flight_tracker": "transportation",
    "aviation_weather": "transportation",
    "ship_tracker": "transportation",
    "velib": "transportation",
    
    # Networking
    "http_client": "networking",
    
    # Utilities
    "math": "utilities",
    "date": "utilities",
    
    # Entertainment
    "chess_com": "entertainment",
    "reddit_intelligence": "entertainment",
}

def update_spec_file(spec_path: Path):
    """Add category field to a spec JSON file."""
    tool_name = spec_path.stem
    
    if tool_name not in CATEGORIES:
        print(f"⚠️  Skipping {tool_name} (no category mapping)")
        return False
    
    category = CATEGORIES[tool_name]
    
    with open(spec_path, 'r', encoding='utf-8') as f:
        spec = json.load(f)
    
    # Check if category already exists
    if 'category' in spec.get('function', {}):
        existing = spec['function']['category']
        if existing == category:
            print(f"✓  {tool_name}: category '{category}' already set")
            return False
        else:
            print(f"⚠️  {tool_name}: updating category '{existing}' -> '{category}'")
    
    # Add category field (after displayName, before description)
    spec['function']['category'] = category
    
    # Rewrite file with proper order
    with open(spec_path, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {tool_name}: added category '{category}'")
    return True

def main():
    specs_dir = Path(__file__).parent / 'src' / 'tool_specs'
    
    if not specs_dir.exists():
        print(f"❌ Directory not found: {specs_dir}")
        return
    
    print(f"📂 Scanning {specs_dir}...\n")
    
    updated_count = 0
    total_count = 0
    
    for spec_file in sorted(specs_dir.glob('*.json')):
        total_count += 1
        if update_spec_file(spec_file):
            updated_count += 1
    
    print(f"\n✨ Done! Updated {updated_count}/{total_count} files")

if __name__ == '__main__':
    main()
