"""Utils and configuration."""
import os
from typing import Dict, Any

def get_ssh_config() -> Dict[str, Any]:
    return {
        "host": os.getenv("LEGI_SSH_HOST", "root@188.245.151.223"),
        "key_path": os.getenv("LEGI_SSH_KEY", "~/.ssh/id_ed25519_legi"),
        "key_passphrase": os.getenv("LEGI_SSH_PASSPHRASE", ""),
        "cli_path": "/root/legifrance/scripts/legi_consult.py"
    }

def build_cli_command(operation: str, **params) -> str:
    config = get_ssh_config()
    cmd = f"sudo -u legifrance_app python3 {config['cli_path']} {operation}"
    
    # list_codes params
    if params.get('scope'):
        cmd += f" --scope {params['scope']}"
    if params.get('nature'):
        cmd += f" --nature {params['nature']}"
    
    # search/tree params
    if params.get('query'):
        cmd += f' --query "{params["query"]}"'
    if params.get('code_id'):
        cmd += f" --code_id {params['code_id']}"
    if params.get('section_id'):
        cmd += f" --section_id {params['section_id']}"
    if params.get('ids'):
        cmd += f" --ids {','.join(params['ids'])}"
    if params.get('etat'):
        cmd += f" --etat {params['etat']}"
    if params.get('limit'):
        cmd += f" --limit {params['limit']}"
    if params.get('max_depth'):
        cmd += f" --max_depth {params['max_depth']}"
    if params.get('max_size_kb'):
        cmd += f" --max_size_kb {params['max_size_kb']}"
        
    # Flags
    if operation == 'get_section_tree':
        if params.get('include_articles') is False:
            cmd += " --no-articles"
            
    return cmd
