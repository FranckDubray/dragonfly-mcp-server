










/**
 * Workers Session - WebSocket & events (strict session.type, stable guards)
 */

function startAutoGreeting(){ autoGreetingTimer = setTimeout(()=>{ if (!userHasSpoken && sessionActive && systemMessageSent && window.sessionUpdatedSent) sendResponseCreateSafe('auto-greeting'); }, 1500); }
function cancelAutoGreeting(){ if (autoGreetingTimer){ clearTimeout(autoGreetingTimer); autoGreetingTimer = null; } }

let lastAssistantFinal = '';
let lastAssistantFinalNorm = '';
let aiStartGraceArmed = false;

const RINGBACK_MIN_MS = 2000;
const RINGBACK_DELAY_ON_AI_MS = 1000;
let ringStopTimer = null;
function stopRingbackRespectingMin(extraDelayMs = 0){
  try{
    if (!window.ringbackTone) return;
    const start = window.__ringStartTs || 0;
    const elapsed = start ? (performance.now() - start) : 0;
    const remainingMin = Math.max(0, RINGBACK_MIN_MS - elapsed);
    const wait = Math.max(remainingMin, extraDelayMs, 0);
    if (window.__DF_DEBUG) console.log('[RINGBACK] stop scheduled(min)', { elapsed: Math.round(elapsed), extraDelayMs, RINGBACK_MIN_MS, wait });
    if (ringStopTimer) { clearTimeout(ringStopTimer); ringStopTimer = null; }
    ringStopTimer = setTimeout(()=>{ try{ ringbackTone.stop(); if (window.__DF_DEBUG) console.log('[RINGBACK] stop called'); }catch(_){ } ringStopTimer=null; }, wait);
  }catch(_){ }
}

function normText(t){ return String(t||'').replace(/\s+/g,' ').replace(/[.!…]+$/,'').trim().toLowerCase(); }

// One-shot patch flag to avoid spamming updates on error
let __sessionTypePatched = false;
// Debounce for first-turn response
let __firstTurnTimer = null;

async function connectWebSocket(url){
  return new Promise((resolve, reject)=>{
    try{
      ws = new WebSocket(url);
      ws.onopen = () => {
        if (window.__DF_DEBUG) console.log('[WS] open');
        try{ stopRingbackRespectingMin(0); }catch(_){ }
        try{
          const instr = String(currentWorkerConfig?.instructions||'');
          const tools = Array.isArray(currentWorkerConfig?.tools) ? currentWorkerConfig.tools : [];
          console.log('[REALTIME] onopen -> session.update', { len: instr.length, tools: tools.map(t=>t?.name||t) });
          const sess = { type:'realtime', instructions: instr, tool_choice: 'auto' };
          if (tools.length){ sess.tools = tools; }
          ws.send(JSON.stringify({ type:'session.update', session: sess }));
          window.sessionUpdatedSent = true;
        }catch(e){ console.warn('[REALTIME] session.update failed to send on open:', e?.message||e); }
        resolve();
      };
      ws.onmessage = (ev) => {
        if (!sessionActive) return;
        try{ const msg = JSON.parse(ev.data); handleRealtimeMessage(msg); }catch(_){ }
      };
      ws.onerror = () => { if (window.__DF_DEBUG) console.log('[WS] error'); try{ stopRingbackRespectingMin(0); }catch(_){ } reject(new Error('WebSocket failed')); };
      ws.onclose = () => { if (window.__DF_DEBUG) console.log('[WS] close'); try{ stopRecording(); }catch(_){ } try{ stopRingbackRespectingMin(0); }catch(_){ } try{ updateVu(currentWorkerIdMemo||'', 0); resetVu(currentWorkerIdMemo||''); setAISpeaking(false); }catch(_){ } sessionActive = false; try{ if (typeof endCall === 'function') endCall(); }catch(_){ } };
    }catch(e){ reject(e); }
  });
}

function handleRealtimeMessage(data){
  if (!sessionActive) return;
  const t = data.type||'';
  if (t !== 'rate_limits.updated' && window.__DF_DEBUG) console.log('[WS EVT]', t, data);

  if (t==='rate_limits.updated') return;

  if (t==='session.created'){
    try{ stopRingbackRespectingMin(0); }catch(_){ }
    if (!systemMessageSent) sendSystemMessage();
    try{
      const instr = String(currentWorkerConfig?.instructions||'');
      const tools = Array.isArray(currentWorkerConfig?.tools) ? currentWorkerConfig.tools : [];
      const sess = { type:'realtime', instructions: instr, tool_choice: 'auto' };
      if (tools.length){ sess.tools = tools; }
      ws.send(JSON.stringify({ type:'session.update', session: sess }));
      window.sessionUpdatedSent = true;
      if (window.__DF_DEBUG) console.log('[REALTIME] session.update on session.created', sess);
    }catch(e){ console.warn('[REALTIME] retry session.update failed:', e?.message||e); }
  }
  if (t==='error'){
    const msg = data.error?.message||'';
    console.error('[REALTIME] Error:', msg);
    // Patch only once if server demands session.type
    if (/session\.type/i.test(msg) && !__sessionTypePatched){
      try{
        const instr = String(currentWorkerConfig?.instructions||'');
        const tools = Array.isArray(currentWorkerConfig?.tools) ? currentWorkerConfig.tools : [];
        const sess = { type:'realtime', instructions: instr, tool_choice: 'auto' };
        if (tools.length){ sess.tools = tools; }
        ws.send(JSON.stringify({ type:'session.update', session: sess }));
        window.sessionUpdatedSent = true;
        __sessionTypePatched = true;
        if (window.__DF_DEBUG) console.log('[REALTIME] session.update (patch type) sent');
      }catch(e){ console.warn('[REALTIME] session.update (patch type) failed:', e?.message||e); }
      return;
    }
    // Active response -> just ignore further creates until done
    if (/active response in progress/i.test(msg)){
      responseCreatePending = false; // drop pending
      return;
    }
    return;
  }
  if (t==='response.created'){
    currentResponseId = data.response?.id||null;
    responseCreatePending = false;
    hasActiveResponse = !!currentResponseId;
    assistantBuffer = "";
    lastAssistantFinal = '';
    lastAssistantFinalNorm = '';
    aiStartGraceArmed = true;
    try{ cancelAutoGreeting(); }catch(_){ }
  }
  if (t==='response.done' || t==='response.cancelled'){
    hasActiveResponse = false;
    currentResponseId = null; window.isUserSpeaking=false; try{ updateVu(currentWorkerIdMemo||'', 0); resetVu(currentWorkerIdMemo||''); setAISpeaking(false); window.aiSpeaking=false; }catch(_){ }
  }

  if (t==='input_audio_buffer.speech_started'){
    if (window.aiGraceUntil && Date.now() < window.aiGraceUntil) { return; }
    window.isUserSpeaking = true; if (!userHasSpoken){ userHasSpoken = true; cancelAutoGreeting(); }
  }
  if (t==='input_audio_buffer.committed'){
    window.isUserSpeaking = false;
    try{ if (userSpeechTimer) clearTimeout(userSpeechTimer); }catch(_){ }
    if (!firstTurnTriggered && !currentResponseId && !hasActiveResponse && systemMessageSent && window.sessionUpdatedSent){
      if (__firstTurnTimer) clearTimeout(__firstTurnTimer);
      __firstTurnTimer = setTimeout(()=>{ sendResponseCreateSafe('first-turn'); firstTurnTriggered = true; }, 300);
    }
  }

  if (t==='response.output_audio_transcript.delta'){
    assistantBuffer += (data.delta||'');
    if (window.__DF_DEBUG) console.log('[TRANSCRIPT.delta]', (data.delta||'').length);
  }
  if (t==='response.output_audio_transcript.done'){
    const finalText = (data.transcript || assistantBuffer || '').trim();
    const norm = normText(finalText);
    if (finalText && norm && norm !== lastAssistantFinalNorm){
      miniAppend('assistant', finalText);
      inlineAppend('assistant', finalText);
      lastAssistantFinal = finalText;
      lastAssistantFinalNorm = norm;
    }
    assistantBuffer = "";
  }
  if (t==='response.output_audio.delta'){
    try{
      window.aiGraceUntil = Date.now() + 500; // 500ms grace to ignore echo-triggered user speech
      stopRingbackRespectingMin(RINGBACK_DELAY_ON_AI_MS); gotFirstAIAudio = true; setAISpeaking(true); window.aiSpeaking=true;
    }catch(_){ }
    try{
      const amp = ampFromPcm16Base64(data.delta||'');
      if (window.__DF_DEBUG) console.log('[VU] output_audio.delta', { bytes: (data.delta||'').length, amp });
      updateVu(currentWorkerIdMemo||'', amp);
    }catch(_){ }
    if (data.delta && window.audioPlayer && !window.isUserSpeaking){ try{ audioPlayer.playBase64Pcm16(data.delta); if (window.__DF_DEBUG) console.log('[AUDIO] queued', (data.delta||'').length, 'bytes'); }catch(_){ } }
  }

  if (t==='response.audio.delta'){
    try{
      window.aiGraceUntil = Date.now() + 500;
      stopRingbackRespectingMin(RINGBACK_DELAY_ON_AI_MS); gotFirstAIAudio = true; setAISpeaking(true); window.aiSpeaking=true;
    }catch(_){ }
    try{
      const amp = ampFromPcm16Base64(data.delta||'');
      if (window.__DF_DEBUG) console.log('[VU] audio.delta', { bytes: (data.delta||'').length, amp });
      updateVu(currentWorkerIdMemo||'', amp);
    }catch(_){ }
    if (data.delta && window.audioPlayer && !window.isUserSpeaking){ try{ audioPlayer.playBase64Pcm16(data.delta); }catch(_){ } }
  }

  if (t==='response.function_call_arguments.done' || t==='response.tool_call_arguments.done' || t==='response.function_call.completed') handleFunctionCall(data);
}

window.connectWebSocket = connectWebSocket;
window.handleRealtimeMessage = handleRealtimeMessage;
