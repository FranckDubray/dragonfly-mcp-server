"""
chat_agent — Multi-turn conversational agent with Platform Threading API.

Persistent conversations with server-side state management.
Supports tool use with full history persistence.

Usage:
    from tools._chat_agent import execute_chat_agent
    
    result = execute_chat_agent(
        message="Hello",
        model="gpt-5.2",
        tools=["date", "math"],
        thread_id=None,  # or existing thread_id
        output_mode="intermediate"
    )
"""

from .agent import execute_chat_agent

__all__ = ["execute_chat_agent"]
