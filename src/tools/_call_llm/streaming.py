"""
Streaming utilities for LLM responses
"""
import json
import logging

LOG = logging.getLogger(__name__)

def process_streaming_chunks(response):
    """
    Process streaming response and return content
    FIXED: All startswith('') are corrected to startswith('data: ')
    """
    content = ""
    finish_reason = None
    usage = None
    chunk_count = 0
    
    for line in response.iter_lines():
        if not line:
            continue
        line = line.decode('utf-8').strip()
        if line.startswith('data: '):  # ✅ FIXED: was '' before
            data_str = line[6:]
            if data_str == '[DONE]':
                break
            try:
                chunk = json.loads(data_str)
                
                # Unwrap response if needed
                if "response" in chunk and "choices" not in chunk:
                    chunk = chunk["response"]
                
                chunk_count += 1
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        content += delta["content"]
                        if LOG.isEnabledFor(logging.DEBUG) and chunk_count <= 3:
                            LOG.debug(f"Chunk {chunk_count}: +'{delta['content']}'")
                    if "finish_reason" in choices[0] and choices[0]["finish_reason"]:
                        finish_reason = choices[0]["finish_reason"]
                if "usage" in chunk:
                    usage = chunk["usage"]
            except:
                continue
    
    if LOG.isEnabledFor(logging.DEBUG):
        LOG.debug(f"← Streaming complete: {chunk_count} chunks, content_len={len(content)}, finish_reason={finish_reason}")
    
    return {
        "content": content,
        "finish_reason": finish_reason or "stop",
        "usage": usage
    }