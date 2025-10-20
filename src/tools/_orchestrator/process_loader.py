# Process loader with $import support + subgraph resolution
# Allows splitting large process files into reusable fragments + hierarchical subgraphs

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Union

class ProcessLoadError(Exception):
    """Raised when process loading fails"""
    pass

def load_process_with_imports(process_file: str, base_dir: str = None) -> Dict:
    """
    Load process JSON with $import resolution + subgraph flattening.
    
    Args:
        process_file: Path to main process file (absolute or relative)
        base_dir: Base directory for resolving relative imports (default: process file's directory)
    
    Returns:
        Fully resolved process dict (all $import replaced + subgraphs flattened)
    
    Raises:
        ProcessLoadError: If file not found or import fails
    
    Example:
        process = load_process_with_imports('workers/ai_curation/main.process.json')
    """
    # Resolve process file path
    process_path = Path(process_file).resolve()
    if not process_path.exists():
        raise ProcessLoadError(
            f"Process file not found: {process_file}\n"
            f"Resolved path: {process_path}\n"
            f"Check that the file exists and path is correct."
        )
    
    # Base directory for relative imports (default: process file's directory)
    if base_dir is None:
        base_dir = process_path.parent
    else:
        base_dir = Path(base_dir).resolve()
    
    # Load main process file
    try:
        with open(process_path, 'r', encoding='utf-8') as f:
            process = json.load(f)
    except json.JSONDecodeError as e:
        raise ProcessLoadError(
            f"Invalid JSON in process file: {process_file}\n"
            f"Error at line {e.lineno}, column {e.colno}: {e.msg}\n"
            f"Check JSON syntax (trailing commas, quotes, brackets)."
        )
    except Exception as e:
        raise ProcessLoadError(
            f"Failed to read process file: {process_file}\n"
            f"Error: {str(e)}"
        )
    
    # Resolve all $import recursively
    try:
        resolved = _resolve_imports(process, base_dir, visited=set())
    except ProcessLoadError:
        raise  # Re-raise with original context
    except Exception as e:
        raise ProcessLoadError(
            f"Unexpected error resolving imports in: {process_file}\n"
            f"Error: {str(e)}"
        )
    
    # Flatten subgraphs if present
    if 'graph' in resolved and 'subgraphs' in resolved.get('graph', {}):
        resolved = _flatten_subgraphs(resolved, base_dir)
    
    return resolved


def _flatten_subgraphs(process: Dict, base_dir: Path) -> Dict:
    """
    Flatten subgraphs into main graph (resolve interfaces entry/exit).
    
    Transforms:
      graph.subgraphs: [{id, import, ...}]
      graph.edges: [{from: "INIT", to: "COLLECT"}]
    
    Into:
      graph.nodes: [all nodes from all subgraphs]
      graph.edges: [resolved inter-subgraph edges + all intra-subgraph edges]
    """
    graph = process.get('graph', {})
    subgraphs_spec = graph.get('subgraphs', [])
    
    if not subgraphs_spec:
        return process  # No subgraphs, nothing to flatten
    
    # Load all subgraphs
    subgraphs = {}  # {id: {nodes, edges, interface}}
    for sg_spec in subgraphs_spec:
        sg_id = sg_spec['id']
        sg_import = sg_spec['import']
        
        # Load subgraph file
        sg_path = (base_dir / sg_import).resolve()
        if not sg_path.exists():
            raise ProcessLoadError(f"Subgraph import not found: {sg_import} (resolved: {sg_path})")
        
        try:
            with open(sg_path, 'r', encoding='utf-8') as f:
                sg_data = json.load(f)
        except Exception as e:
            raise ProcessLoadError(f"Failed to load subgraph {sg_import}: {e}")
        
        # Resolve imports within subgraph
        sg_data = _resolve_imports(sg_data, sg_path.parent, visited=set())
        
        subgraphs[sg_id] = sg_data
    
    # Collect all nodes
    all_nodes = list(graph.get('nodes', []))  # START, EXIT from main
    for sg_data in subgraphs.values():
        all_nodes.extend(sg_data.get('nodes', []))
    
    # Resolve inter-subgraph edges
    main_edges = graph.get('edges', [])
    resolved_edges = []
    
    for edge in main_edges:
        from_node = edge['from']
        to_node = edge['to']
        when = edge.get('when', 'always')
        
        # Check if from/to are subgraph IDs
        from_real = _resolve_subgraph_node(from_node, subgraphs, 'exit', when)
        to_real = _resolve_subgraph_node(to_node, subgraphs, 'entry')
        
        resolved_edges.append({
            'from': from_real,
            'to': to_real,
            'when': when
        })
    
    # Add all intra-subgraph edges
    for sg_data in subgraphs.values():
        resolved_edges.extend(sg_data.get('edges', []))
    
    # Rebuild graph
    process['graph']['nodes'] = all_nodes
    process['graph']['edges'] = resolved_edges
    
    # Remove subgraphs spec (now flattened)
    del process['graph']['subgraphs']
    
    return process


def _resolve_subgraph_node(node_ref: str, subgraphs: Dict, interface_type: str, when: str = None) -> str:
    """
    Resolve subgraph ID to real node name using interface.
    
    Args:
        node_ref: Node name or subgraph ID
        subgraphs: {id: {interface: {entry, exits}, ...}}
        interface_type: "entry" or "exit"
        when: route label (for exit resolution)
    
    Returns:
        Real node name
    """
    # If node_ref is a known subgraph ID, resolve via interface
    if node_ref in subgraphs:
        interface = subgraphs[node_ref].get('interface', {})
        
        if interface_type == 'entry':
            entry = interface.get('entry')
            if not entry:
                raise ProcessLoadError(f"Subgraph {node_ref} missing interface.entry")
            return entry
        
        elif interface_type == 'exit':
            exits = interface.get('exits', {})
            
            # Try to match when label
            if when and when != 'always' and when in exits:
                return exits[when]
            
            # Fallback to 'success' exit
            if 'success' in exits:
                return exits['success']
            
            # If only one exit, use it
            if len(exits) == 1:
                return list(exits.values())[0]
            
            raise ProcessLoadError(
                f"Subgraph {node_ref} exit ambiguous: when={when}, available exits={list(exits.keys())}"
            )
    
    # Not a subgraph ID, return as-is (real node name)
    return node_ref


def _resolve_imports(data: Any, base_dir: Path, visited: set, depth: int = 0) -> Any:
    """
    Recursively resolve $import in data structure.
    
    Args:
        data: Data structure (dict, list, or primitive)
        base_dir: Base directory for resolving relative paths
        visited: Set of visited file paths (cycle detection)
        depth: Current recursion depth (max 10)
    
    Returns:
        Resolved data with all $import replaced
    """
    # Guard: max depth to prevent infinite recursion
    if depth > 10:
        raise ProcessLoadError(
            f"Max import depth (10) exceeded - possible circular dependency.\n"
            f"Import chain is too deep. Check for circular imports or excessive nesting.\n"
            f"Current base directory: {base_dir}"
        )
    
    # Dict: check for $import key or recurse
    if isinstance(data, dict):
        if "$import" in data:
            return _load_import(data["$import"], base_dir, visited, depth)
        else:
            # Recurse into all dict values
            return {k: _resolve_imports(v, base_dir, visited, depth + 1) for k, v in data.items()}
    
    # List: check each item for $import or recurse
    elif isinstance(data, list):
        resolved = []
        for item in data:
            if isinstance(item, dict) and "$import" in item:
                # Import can return single item or array
                imported = _load_import(item["$import"], base_dir, visited, depth)
                if isinstance(imported, list):
                    resolved.extend(imported)  # Flatten array
                else:
                    resolved.append(imported)
            else:
                resolved.append(_resolve_imports(item, base_dir, visited, depth + 1))
        return resolved
    
    # Primitives: return as-is
    else:
        return data


def _candidate_import_paths(base_dir: Path, import_path: str) -> List[Path]:
    """Return candidate absolute paths for an import, in priority order.
    1) base_dir / import_path
    2) base_dir / 'nodes' / import_path  (allow keeping JSON snippets under a local nodes/ folder)
    """
    paths: List[Path] = []
    p1 = (base_dir / import_path).resolve()
    paths.append(p1)
    p2 = (base_dir / 'nodes' / import_path).resolve()
    if p2 not in paths:
        paths.append(p2)
    return paths


def _load_import(import_path: str, base_dir: Path, visited: set, depth: int) -> Any:
    """
    Load and resolve a single $import.
    
    Args:
        import_path: Relative path to file (e.g., "prompts/sonar_fetch.json" or "node_x.json")
        base_dir: Base directory for resolving path
        visited: Set of visited files (cycle detection)
        depth: Current depth
    
    Returns:
        Loaded and resolved content
    """
    last_err = None
    candidates = _candidate_import_paths(base_dir, import_path)
    candidates_str = "\n  - ".join(str(p) for p in candidates)

    for candidate in candidates:
        try:
            # Check if file exists
            if not candidate.exists():
                continue
            
            # Cycle detection
            candidate_str = str(candidate)
            if candidate_str in visited:
                raise ProcessLoadError(
                    f"Circular import detected!\n"
                    f"Import path: {import_path}\n"
                    f"File already visited: {candidate}\n"
                    f"Import chain: {' -> '.join(sorted(visited))}\n"
                    f"Check for circular dependencies in your $import declarations."
                )
            visited.add(candidate_str)
            
            # Load file
            try:
                with open(candidate, 'r', encoding='utf-8') as f:
                    imported = json.load(f)
            except json.JSONDecodeError as e:
                raise ProcessLoadError(
                    f"Invalid JSON in imported file: {import_path}\n"
                    f"Resolved to: {candidate}\n"
                    f"Error at line {e.lineno}, column {e.colno}: {e.msg}\n"
                    f"Check JSON syntax (trailing commas, quotes, brackets)."
                )
            except Exception as e:
                raise ProcessLoadError(
                    f"Failed to read imported file: {import_path}\n"
                    f"Resolved to: {candidate}\n"
                    f"Error: {str(e)}"
                )
            
            # Recursively resolve imports in loaded content
            resolved = _resolve_imports(imported, candidate.parent, visited, depth + 1)
            
            # Remove from visited after processing (allow reuse in different branches)
            visited.discard(candidate_str)
            return resolved
        
        except ProcessLoadError as e:
            last_err = e
            break
        except Exception as e:
            last_err = ProcessLoadError(
                f"Unexpected error loading import: {import_path}\n"
                f"Tried: {candidate}\n"
                f"Error: {str(e)}"
            )
            break

    # If none of the candidates worked, raise a helpful error
    if last_err is not None:
        raise last_err
    
    raise ProcessLoadError(
        f"Import file not found: {import_path}\n"
        f"Searched in:\n  - {candidates_str}\n"
        f"Base directory: {base_dir}\n\n"
        f"Tip: Imported files can be placed in:\n"
        f"  1. Same directory as process file\n"
        f"  2. 'nodes/' subdirectory (recommended for organization)\n\n"
        f"Check:\n"
        f"  - File name spelling and extension (.json)\n"
        f"  - Relative path from {base_dir}\n"
        f"  - File permissions (readable)"
    )
