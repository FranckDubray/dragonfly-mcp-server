from typing import Dict

EXT_TO_LANG: Dict[str, str] = {
    # Python
    "py": "python",
    "pyi": "python",
    # JavaScript/TypeScript (future connectors)
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    # Others (placeholders)
    "go": "go",
    "java": "java",
    "kt": "kotlin",
    "kts": "kotlin",
    "rs": "rust",
    "c": "c",
    "h": "c",
    "cc": "cpp",
    "cpp": "cpp",
    "hpp": "cpp",
    "cs": "csharp",
    "php": "php",
    "rb": "ruby",
    "html": "html",
    "css": "css",
    "scss": "css",
    "sql": "sql",
    "yml": "yaml",
    "yaml": "yaml",
    "json": "json",
    "toml": "toml",
    "md": "markdown",
}


def language_from_path(path: str) -> str | None:
    if "." not in path:
        return None
    ext = path.rsplit(".", 1)[-1].lower()
    return EXT_TO_LANG.get(ext)
