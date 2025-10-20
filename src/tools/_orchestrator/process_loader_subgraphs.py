# Process loader - Subgraph flattening (<4KB)

import json
from pathlib import Path
from typing import Dict, List
from .process_loader_imports import resolve_imports_recursive, ProcessLoadError


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


def flatten_subgraphs(process: Dict, base_dir: Path) -> Dict:
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
        return process
    
    # Load all subgraphs
    subgraphs = {}
    for sg_spec in subgraphs_spec:
        sg_id = sg_spec['id']
        sg_import = sg_spec['import']
        
        sg_path = (base_dir / sg_import).resolve()
        if not sg_path.exists():
            raise ProcessLoadError(f"Subgraph import not found: {sg_import} (resolved: {sg_path})")
        
        try:
            with open(sg_path, 'r', encoding='utf-8') as f:
                sg_data = json.load(f)
        except Exception as e:
            raise ProcessLoadError(f"Failed to load subgraph {sg_import}: {e}")
        
        # Resolve imports within subgraph
        sg_data = resolve_imports_recursive(sg_data, sg_path.parent, visited=set())
        
        subgraphs[sg_id] = sg_data
    
    # Collect all nodes
    all_nodes = list(graph.get('nodes', []))
    for sg_data in subgraphs.values():
        all_nodes.extend(sg_data.get('nodes', []))
    
    # Resolve inter-subgraph edges
    main_edges = graph.get('edges', [])
    resolved_edges = []
    
    for edge in main_edges:
        from_node = edge['from']
        to_node = edge['to']
        when = edge.get('when', 'always')
        
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
