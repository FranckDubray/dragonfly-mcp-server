"""Thread chain builder for Platform Threading API.

Ensures strict linear chain of messages with correct id/parentId/level.
Prevents UI branching by maintaining monotonic level increments.

CRITICAL RULES:
1. id != parentId (always)
2. parentId points to last known message
3. level increments by 1 per message
4. First message has parentId = ROOT_PARENT_ID
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import time
import random
import string

ROOT_PARENT_ID = "000170695000"


def _gen_id(prefix: str = "m") -> str:
    """Generate unique message ID (timestamp-random)."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
    return f"{int(time.time() * 1000)}-{prefix}-{suffix}"


class ThreadChain:
    """Manages message chain with id/parentId/level for Threading API."""
    
    def __init__(self, last_id: Optional[Any] = None, last_level: int = -1):
        """Initialize chain state.
        
        Args:
            last_id: ID of the last message in the chain (or ROOT for empty)
            last_level: Level of the last message (-1 for empty thread)
        """
        self.last_id = last_id if last_id else ROOT_PARENT_ID
        self.last_level = int(last_level)
    
    @classmethod
    def from_messages(cls, messages: List[Dict[str, Any]]) -> "ThreadChain":
        """Create chain from existing messages history.
        
        Args:
            messages: List of messages with id/level fields
        
        Returns:
            Threin initialized to continue from last message
        """
        if not messages:
            return cls(last_id=ROOT_PARENT_ID, last_level=-1)
        
        last = messages[-1]
        return cls(
            last_id=last.get("id"),
            last_level=int(last.get("level", 0))
        )
    
    def _next_level(self) -> int:
        """Calculate next level."""
        return self.last_level + 1
    
    def _parent(self) -> Any:
        """Get parent ID for next message."""
        return self.last_id
    
    def new_user(self, text: str) -> Dict[str, Any]:
        """Create a new user message.
        
        Args:
            text: User message content
        
        Returns:
            Message dict with role/content/id/parentId/level
        """
        mid = _gen_id("u")
        pid = self._parent()
        lvl = self._next_level()
        
        msg = {
            "role": "user",
            "content": [{"type": "text", "text": text}],
            "id": mid,
            "parentId": pid,
            "level": lvl,
        }
        
        # Update state
        self.last_id = mid
        self.last_level = lvl
        
        return msg
    
    def new_assistant_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create assistant message with tool_calls.
        
        Args:
            tool_calls: OpenAI-format tool_calls (normalized)
        
        Returns:
            Message dict with role/tool_calls/id/parentId/level
        """
        # Normalize tool_calls to ensure OpenAI compliance
        normalized = self._normalize_tool_calls(tool_calls)
        
        mid = _gen_id("a")
        pid = self._parent()
        lvl = self._next_level()
        
        msg = {
            "role": "assistant",
            "tool_calls": normalized,
            "id": mid,
            "parentId": pid,
            "level": lvl,
        }
        
        # Update state
        self.last_id = mid
        self.last_level = lvl
        
        return msg
    
    def new_tool_result(self, tool_call_id: str, content_text: str) -> Dict[str, Any]:
        """Create a tool result message.
        
        Args:
            tool_call_id: ID of the tool_call this result corresponds to
            content_text: JSON-stringified tool result
        
        Returns:
            Message dict with role/tool_call_id/content/id/parentId/level
        """
        mid = _gen_id("t")
        pid = self._parent()
        lvl = self._next_level()
        
        msg = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content_text,
            "id": mid,
            "parentId": pid,
            "level": lvl,
        }
        
        # Update state
        self.last_id = mid
        self.last_level = lvl
        
        return msg
    
    def new_assistant_text(self, text: str) -> Dict[str, Any]:
        """Create final assistant text message.
        
        Args:
            text: Assistant response content
        
        Returns:
            Message dict with role/content/id/parentId/level
        """
        mid = _gen_id("asst")
        pid = self._parent()
        lvl = self._next_level()
        
        msg = {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
            "id": mid,
            "parentId": pid,
            "level": lvl,
        }
        
        # Update state
        self.last_id = mid
        self.last_level = lvl
        
        return msg
    
    def commit_assistant_id(self, platform_id: Any) -> None:
        """Update chain with real assistant ID from platform.
        
        Call this after receiving the assistant response with real ID.
        
        Args:
            platform_id: ID returned by Platform API (e.g., "chatcmpl-xxx")
        """
        if platform_id:
            self.last_id = platform_id
            # Level already incremented when message was created
    
    def _normalize_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure each tool_call has id, type, and function{name, arguments(str)}.
        
        This prevents API validation errors and UI corruption.
        """
        import json
        
        normalized: List[Dict[str, Any]] = []
        
        for tc in tool_calls or []:
            tc = dict(tc) if isinstance(tc, dict) else {}
            
            # Ensure id
            if not tc.get("id"):
                tc["id"] = f"call_{_gen_id('tc')}"
            
            # Ensure type
            if not tc.get("type"):
                tc["type"] = "function"
            
            # Ensure function dict
            fn = tc.get("function") if isinstance(tc.get("function"), dict) else None
            if not fn:
                # Fallback to old shape
                fname = tc.get("name")
                fargs = tc.get("arguments") or "{}"
                fn = {"name": fname, "arguments": fargs}
            
            # Ensure arguments is string
            args = fn.get("arguments")
            if args is None:
                args = "{}"
            if not isinstance(args, str):
                args = json.dumps(args)
            
            tc["function"] = {
                "name": fn.get("name"),
                "arguments": args
            }
            
            normalized.append(tc)
        
        return normalized
    
    def get_state(self) -> Dict[str, Any]:
        """Get current chain state for debugging."""
        return {
            "last_id": self.last_id,
            "last_level": self.last_level,
        }
