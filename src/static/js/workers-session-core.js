










/**
 * Workers Session - Core (start/stop + system message + response create)
 */

function htmlEscape(s){ return String(s || '').replace(/&/g,'&').replace(/</g,'<').replace(/>/g,'>'); }
function miniAppend(role, text){
  const body = document.getElementById('miniTranscriptsBody'); if (!body) return;
  const ts = new Date(); const hh = String(ts.getHours()).padStart(2,'0'); const mm = String(ts.getMinutes()).padStart(2,'0');
  const time = `${hh}:${mm}`;
  body.insertAdjacentHTML('beforeend', `<div class="mini-line"><span class="t">${time}</span> <span class="r ${role}">${role==='vous'?'Vous':(role==='tool'?'Tool':'Assistant')}</span> <span class="m">${htmlEscape(text)}</span></div>`);
  try{ body.scrollTop = body.scrollHeight; body.lastElementChild?.scrollIntoView({block:'end'}); }catch(_){ }
}
function inlineAppend(role, text){ /* no-op by design */ }
function safeArgsPreview(obj){ try{ const s = JSON.stringify(obj); return s.length>400? s.slice(0,380)+'…' : s; }catch(_){ return String(obj);} }

let lastResponseCreateTs = 0;
let callStartTs = null; // NEW: call start timestamp
let callTimer = null;

async function startRealtimeSession(config) {
  currentWorkerConfig = { worker_id: config.worker_id };
  currentWorkerIdMemo = config.worker_id;
  userHasSpoken = false; firstTurnTriggered = false; gotFirstAIAudio = false;
  currentResponseId = null; responseCreatePending = false; window.isUserSpeaking = false; systemMessageSent = false; sessionActive = true; assistantBuffer = "";

  try {
    const startUrl = `/workers/${config.worker_id}/realtime/start`;
    if (window.__DF_DEBUG) console.log('[REALTIME START] POST', startUrl);
    const sessionResp = await fetch(startUrl, { method: 'POST', headers: {'Content-Type': 'application/json'} });
    if (!sessionResp.ok) {
      let txt = '';
      try { txt = await sessionResp.text(); } catch(_){ }
      console.error('[REALTIME START] failed', sessionResp.status, txt);
      throw new Error(`HTTP ${sessionResp.status} ${txt||''}`);
    }
    const sessionData = await sessionResp.json();
    if (!sessionData.id || !sessionData.websocketUrl || !sessionData.sessionToken) throw new Error('Invalid session data');

    // Seed config from session response if present
    currentWorkerConfig.instructions = sessionData.instructions || '';
    currentWorkerConfig.tools = Array.isArray(sessionData.tools) ? sessionData.tools : [];
    currentWorkerConfig.voice = sessionData.voice || currentWorkerConfig.voice || '';
    currentWorkerConfig.modalities = Array.isArray(sessionData.modalities) ? sessionData.modalities : (currentWorkerConfig.modalities||['text','audio']);
    currentWorkerConfig.input_audio_format = sessionData.input_audio_format || currentWorkerConfig.input_audio_format || 'pcm16';
    currentWorkerConfig.output_audio_format = sessionData.output_audio_format || currentWorkerConfig.output_audio_format || 'pcm16';
    currentWorkerConfig.turn_detection = sessionData.turn_detection || currentWorkerConfig.turn_detection || null;

    sessionId = sessionData.id;
    await connectWebSocket(`${sessionData.websocketUrl}?token=${encodeURIComponent(sessionData.sessionToken)}`);

    try{ const body = document.getElementById('miniTranscriptsBody'); if (body) body.innerHTML = ''; }catch(_){ }

    // Envoie un session.update complet après le system message (sécurité)
    setTimeout(()=>{
      try{
        if (!systemMessageSent && ws && ws.readyState===WebSocket.OPEN){
          sendSystemMessage();
        }
        if (ws && ws.readyState===WebSocket.OPEN){
          const sess = { type:'realtime', instructions: currentWorkerConfig.instructions||'', tool_choice:'auto' };
          if (Array.isArray(currentWorkerConfig.tools) && currentWorkerConfig.tools.length){ sess.tools = currentWorkerConfig.tools; }
          ws.send(JSON.stringify({ type:'session.update', session: sess }));
          if (window.__DF_DEBUG) console.log('[REALTIME] session.update (post-init) sent', sess);
          window.sessionUpdatedSent = true;
        }
      }catch(_){ }
    }, 800);

    await startRecording();
    startAutoGreeting();

    callStartTs = Date.now();
    if (callTimer) clearInterval(callTimer);
    callTimer = setInterval(updateCallDurationUI, 1000);
    updateCallDurationUI();
  } catch (e) {
    try { if (window.ringbackTone) ringbackTone.stop(); } catch(_){ }
    console.error('[REALTIME START] Exception', e);
    alert(`Erreur: ${e.message}`);
    try { if (typeof endCall === 'function') endCall(); } catch(_){ }
  }
}

function updateCallDurationUI(){
  try{
    if (!callStartTs) return;
    const t = Math.floor((Date.now() - callStartTs)/1000);
    const m = String(Math.floor(t/60)).padStart(2,'0');
    const s = String(t%60).padStart(2,'0');
    let badge = document.getElementById('callDuration');
    if (!badge){
      const hdr = document.querySelector('.header-right');
      if (!hdr) return;
      badge = document.createElement('span');
      badge.id = 'callDuration';
      badge.className = 'chip';
      hdr.appendChild(badge);
    }
    badge.textContent = `⏱ ${m}:${s}`;
  }catch(_){ }
}

function sendSystemMessage(){
  if (!ws || ws.readyState!==WebSocket.OPEN || !currentWorkerConfig) return;
  const instructions = currentWorkerConfig.instructions || '🇫🇷 Parler en français.';
  // Use input_text only (older Realtime expects input_text)
  const sysItemInputText = { type:'input_text', text: instructions };
  const payload = { type:'conversation.item.create', item:{ type:'message', role:'system', content:[sysItemInputText] } };
  try{
    ws.send(JSON.stringify(payload));
    if (window.__DF_DEBUG) console.log('[REALTIME] system message (input_text) sent, len=', instructions.length);
    systemMessageSent = true;
  }catch(e){ console.warn('[REALTIME] system message send failed', e?.message||e); }
}

function sendResponseCreateSafe(){
  if (!ws || ws.readyState!==WebSocket.OPEN) return;
  if (!window.sessionUpdatedSent) return; // ensure instructions applied
  if (window.isUserSpeaking) return;
  if (currentResponseId) return;
  if (responseCreatePending) return;
  if (hasActiveResponse) return; // guard
  try{ if (window.userLastSpeechMs && window.userLastSpeechMs < 500) return; }catch(_){ }
  const now = Date.now();
  if (now - lastResponseCreateTs < 1400) return; // throttle renforcé
  try{
    responseCreatePending=true;
    hasActiveResponse=true; // mark busy immediately to avoid double submit
    lastResponseCreateTs = now;
    ws.send(JSON.stringify({type:'response.create'}));
  }catch(_){ responseCreatePending=false; hasActiveResponse=false; }
}

function closeSession(){
  try{ if (ws && ws.readyState === WebSocket.OPEN) ws.close(1000, 'client_hangup'); }catch(_){ }
  try{ stopRecording(); }catch(_){ }
  try{ audioPlayer?.stopAll?.(); }catch(_){ }
  try{ ringbackTone?.stop?.(); }catch(_){ }
  try{ setAISpeaking(false); resetVu(currentWorkerIdMemo||''); }catch(_){ }
  sessionActive = false;
  if (callTimer) clearInterval(callTimer); callTimer=null; callStartTs=null;
}

window.startRealtimeSession = startRealtimeSession;
window.sendSystemMessage = sendSystemMessage;
window.sendResponseCreateSafe = sendResponseCreateSafe;
window.closeSession = closeSession;
