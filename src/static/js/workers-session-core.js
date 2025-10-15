/**
 * Workers Session - Core (start/stop + system message + response create)
 */

function htmlEscape(s){ return String(s || '').replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>'); }
function miniAppend(role, text){ const body = document.getElementById('miniTranscriptsBody'); if (!body) return; const ts = new Date(); const hh = String(ts.getHours()).padStart(2,'0'); const mm = String(ts.getMinutes()).padStart(2,'0'); const time = `${hh}:${mm}`; body.insertAdjacentHTML('beforeend', `<div class="mini-line"><span class="t">${time}</span> <span class="r ${role}">${role==='vous'?'Vous':(role==='tool'?'Tool':'Assistant')}</span> <span class="m">${htmlEscape(text)}</span></div>`); body.scrollTop = body.scrollHeight; }
function inlineAppend(role, text){ /* no-op by design */ }
function safeArgsPreview(obj){ try{ const s = JSON.stringify(obj); return s.length>400? s.slice(0,380)+'…' : s; }catch(_){ return String(obj);} }

let lastResponseCreateTs = 0;

async function startRealtimeSession(config) {
  currentWorkerConfig = { worker_id: config.worker_id };
  currentWorkerIdMemo = config.worker_id;
  userHasSpoken = false; firstTurnTriggered = false; gotFirstAIAudio = false;
  currentResponseId = null; responseCreatePending = false; window.isUserSpeaking = false; systemMessageSent = false; sessionActive = true; assistantBuffer = "";

  try {
    const startUrl = `/workers/${config.worker_id}/realtime/start`;
    const sessionResp = await fetch(startUrl, { method: 'POST', headers: {'Content-Type': 'application/json'} });
    if (!sessionResp.ok) throw new Error(`HTTP ${sessionResp.status}`);
    const sessionData = await sessionResp.json();
    if (!sessionData.id || !sessionData.websocketUrl || !sessionData.sessionToken) throw new Error('Invalid session data');

    currentWorkerConfig.instructions = sessionData.instructions || '';
    currentWorkerConfig.tools = sessionData.tools || [];

    console.info('[REALTIME] Instructions length:', (currentWorkerConfig.instructions||'').length, 'preview:', (currentWorkerConfig.instructions||'').slice(0,120));
    console.info('[REALTIME] Tools included:', (currentWorkerConfig.tools||[]).map(t=>t?.name || t));

    sessionId = sessionData.id;
    await connectWebSocket(`${sessionData.websocketUrl}?token=${encodeURIComponent(sessionData.sessionToken)}`);

    // Fallback si session.created absent
    setTimeout(()=>{
      try{
        if (!systemMessageSent && ws && ws.readyState===WebSocket.OPEN){
          console.warn('[REALTIME] session.created non reçu, fallback system + session.update');
          sendSystemMessage();
          if (Array.isArray(currentWorkerConfig.tools) && currentWorkerConfig.tools.length){
            ws.send(JSON.stringify({ type:'session.update', session:{ type:'realtime', instructions: currentWorkerConfig.instructions||'', tools: currentWorkerConfig.tools, tool_choice: 'auto' } }));
          }
        }
      }catch(_){ }
    }, 800);

    await startRecording();
    startAutoGreeting();
  } catch (e) {
    try { if (window.ringbackTone) ringbackTone.stop(); } catch(_){}
    alert(`Erreur: ${e.message}`);
    try { if (typeof endCall === 'function') endCall(); } catch(_){}
  }
}

function sendSystemMessage(){
  if (!ws || ws.readyState!==WebSocket.OPEN || !currentWorkerConfig) return;
  const instructions = currentWorkerConfig.instructions || '🇫🇷 Parler en français.';
  if (!currentWorkerConfig.instructions){ console.warn('[REALTIME] Aucune instruction DB fournie, fallback FR.'); }
  miniAppend('assistant','(contexte système chargé)'); inlineAppend('assistant','(contexte système chargé)');
  ws.send(JSON.stringify({ type:'conversation.item.create', item:{ type:'message', role:'system', content:[{ type:'input_text', text: instructions }] } }));
  systemMessageSent = true;
}

function sendResponseCreateSafe(){
  if (!ws || ws.readyState!==WebSocket.OPEN) return;
  if (window.isUserSpeaking) return;
  if (currentResponseId) return;
  if (responseCreatePending) return;
  const now = Date.now();
  if (now - lastResponseCreateTs < 1200) return; // throttle
  try{
    responseCreatePending=true;
    lastResponseCreateTs = now;
    ws.send(JSON.stringify({type:'response.create'}));
  }catch(_){ responseCreatePending=false; }
}

function closeSession(){
  try{ if (ws && ws.readyState === WebSocket.OPEN) ws.close(1000, 'client_hangup'); }catch(_){ }
  try{ stopRecording(); }catch(_){ }
  try{ audioPlayer?.stopAll?.(); }catch(_){ }
  try{ ringbackTone?.stop?.(); }catch(_){ }
  try{ setAISpeaking(false); resetVu(currentWorkerIdMemo||''); }catch(_){ }
  sessionActive = false;
}

// Expose
window.startRealtimeSession = startRealtimeSession;
window.sendSystemMessage = sendSystemMessage;
window.sendResponseCreateSafe = sendResponseCreateSafe;
window.closeSession = closeSession;
