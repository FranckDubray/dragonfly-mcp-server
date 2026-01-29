"""
LLM Agent with multi-turn tool orchestration.

Allows the LLM to call tools in sequence, using previous results
to decide next calls. Stops naturally when finish_reason="stop".
"""
from .core import execute_agent

__all__ = ["execute_agent"]
