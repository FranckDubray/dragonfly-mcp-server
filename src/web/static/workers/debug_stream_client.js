

















// Legacy debug stream client removed (SSE/NDJSON via /workers/api/debug/stream)
// The app now relies on observe (poll) through /execute (py_orchestrator operation=observe).
// This module is kept as a no-op shim to avoid import errors; it exposes a stub that does nothing.

export function setupDebugStream(worker, onEvent){
  console.info('[debug_stream_client] disabled: use observe (poll) instead');
  return () => { /* noop */ };
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
