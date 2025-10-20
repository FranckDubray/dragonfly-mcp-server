# Orchestrator - Edge traversal and routing (<2KB)

from typing import Dict, List, Optional


def get_available_routes(from_node: str, edges: List[Dict]) -> list:
    """
    Get available routes (when labels) from a node.
    
    Args:
        from_node: Source node name
        edges: All edges in graph
    
    Returns:
        List of route labels (excluding 'always')
    """
    routes = []
    for edge in edges:
        if edge['from'] == from_node:
            when = edge.get('when', 'always')
            if when != 'always':
                routes.append(when)
    return routes


def follow_edge(from_node: str, route: str, edges: List[Dict]) -> Optional[str]:
    """
    Follow an edge from a node with a given route.
    
    Args:
        from_node: Source node name
        route: Route label (e.g., 'true', 'false', 'SPAM')
        edges: All edges in graph
    
    Returns:
        Target node name, or None if no edge found
    """
    for edge in edges:
        if edge['from'] == from_node:
            when = edge.get('when', 'always')
            if when == route or when == 'always':
                return edge['to']
    return None


def get_scope_trigger(from_node: str, route: str, edges: List[Dict]) -> Optional[Dict]:
    """
    Get scope trigger from edge if present.
    
    Args:
        from_node: Source node name
        route: Route label
        edges: All edges in graph
    
    Returns:
        Scope trigger dict or None
    """
    for edge in edges:
        if edge['from'] == from_node:
            when = edge.get('when', 'always')
            if when == route or when == 'always':
                return edge.get('scope_trigger')
    return None
