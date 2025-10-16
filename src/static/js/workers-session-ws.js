

/**
 * Workers Session - WebSocket & events
 */

function startAutoGreeting(){ autoGreetingTimer = setTimeout(()=>{ if (!userHasSpoken && sessionActive) sendResponseCreateSafe('auto-greeting'); }, 3000); }
function cancelAutoGreeting(){ if (autoGreetingTimer){ clearTimeout(autoGreetingTimer); autoGreetingTimer = null; } }

let lastAssistantFinal = '';
let lastAssistantFinalNorm = '';
let aiStartGraceArmed = false; // arm a short grace window when AI starts

function normText(t){ return String(t||'').replace(/\s+/g,' ').replace(/[.!…]+$/,'').trim().toLowerCase(); }

async function connectWebSocket(url){
  return new Promise((resolve, reject)=>{
    try{
      ws = new WebSocket(url);
      ws.onopen = ()=>{
        try{ ringbackTone?.stop?.(); }catch(_){ }
        try{
          // Log complet des instructions et outils EXACTEMENT envoyés
          const instr = String(currentWorkerConfig?.instructions||'');
          const tools = Array.isArray(currentWorkerConfig?.tools) ? currentWorkerConfig.tools : [];
          console.log('[REALTIME] Instructions length:', instr.length);
          console.log('[REALTIME] Instructions (FULL):\n', instr);
          console.log('[REALTIME] Tools included:', tools.map(t=>t?.name||t));
          // Envoyer session.update avec instructions & tools
          if (tools.length){
            ws.send(JSON.stringify({ type:'session.update', session:{ type:'realtime', instructions: instr, tools, tool_choice: 'auto' } }));
          } else {
            ws.send(JSON.stringify({ type:'session.update', session:{ type:'realtime', instructions: instr, tool_choice: 'auto' } }));
          }
        }catch(e){ console.warn('[REALTIME] session.update failed to send on open:', e?.message||e); }
        resolve();
      };
      ws.onmessage = (ev)=>{ if (!sessionActive) return; try{ handleRealtimeMessage(JSON.parse(ev.data)); }catch(_){ } };
      ws.onerror = ()=>{ try{ ringbackTone?.stop?.(); }catch(_){ } reject(new Error('WebSocket failed')); };
      ws.onclose = ()=>{ try{ stopRecording(); }catch(_){ } try{ ringbackTone?.stop?.(); }catch(_){ } try{ updateVu(currentWorkerIdMemo||'', 0); resetVu(currentWorkerIdMemo||''); setAISpeaking(false); }catch(_){ } sessionActive = false; try{ if (typeof endCall === 'function') endCall(); }catch(_){ } };
    }catch(e){ reject(e); }
  });
}

function handleRealtimeMessage(data){
  if (!sessionActive) return;
  const t = data.type||'';
  if (t==='session.created'){
    try{ ringbackTone?.stop?.(); }catch(_){ }
    if (!systemMessageSent) sendSystemMessage();
  }
  if (t==='error'){
    try{ ringbackTone?.stop?.(); }catch(_){ }
    const msg = data.error?.message||'';
    if (msg.includes('active response')) responseCreatePending = false;
    console.error('[REALTIME] Error:', msg);
    if (/session\.type/i.test(msg)){
      try{
        const instr = String(currentWorkerConfig?.instructions||'');
        const tools = Array.isArray(currentWorkerConfig?.tools) ? currentWorkerConfig.tools : [];
        console.log('[REALTIME][RETRY] Instructions length:', instr.length);
        console.log('[REALTIME][RETRY] Instructions (FULL):\n', instr);
        console.log('[REALTIME][RETRY] Tools included:', tools.map(t=>t?.name||t));
        ws.send(JSON.stringify({ type:'session.update', session:{ type:'realtime', instructions: instr, tools: tools||[], tool_choice: 'auto' } }));
      }catch(e){ console.warn('[REALTIME] retry session.update failed:', e?.message||e); }
    }
  }
  if (t==='response.created'){
    currentResponseId = data.response?.id||null;
    responseCreatePending = false;
    assistantBuffer = ""; // reset pour la nouvelle réponse
    lastAssistantFinal = '';
    lastAssistantFinalNorm = '';
    aiStartGraceArmed = true; // prochain premier delta audio déclenchera la grace window
  }
  if (t==='response.done' || t==='response.cancelled'){
    currentResponseId = null; window.isUserSpeaking=false; try{ updateVu(currentWorkerIdMemo||'', 0); resetVu(currentWorkerIdMemo||''); setAISpeaking(false); window.aiSpeaking=false; }catch(_){ }
  }

  if (t==='input_audio_buffer.speech_started'){
    // Protection grace window: si l'IA vient juste de démarrer, ignorer de courts bruits ambiants
    if (window.aiGraceUntil && Date.now() < window.aiGraceUntil) {
      return; // ignore ce speech_started (pas de cancel IA, pas de stop audio)
    }
    window.isUserSpeaking = true; if (!userHasSpoken){ userHasSpoken = true; cancelAutoGreeting(); }
    if (currentResponseId && window.audioPlayer) audioPlayer.stopAll();
    if (currentResponseId && ws?.readyState===WebSocket.OPEN){ ws.send(JSON.stringify({type:'response.cancel', response_id: currentResponseId})); }
  }
  if (t==='input_audio_buffer.committed'){
    window.isUserSpeaking = false;
    if (!firstTurnTriggered && !currentResponseId){ sendResponseCreateSafe('first-turn'); firstTurnTriggered = true; }
  }

  if (t==='response.output_audio_transcript.delta'){
    assistantBuffer += (data.delta||'');
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
    try{ ringbackTone?.stop?.(); gotFirstAIAudio = true; setAISpeaking(true); window.aiSpeaking=true; }catch(_){ }
    // Grace window anti-coupure au début de la parole IA (echo/bruit ambiant)
    try{ if (aiStartGraceArmed){ window.aiGraceUntil = Date.now()+350; aiStartGraceArmed = false; } }catch(_){ }
    try{
      const amp = ampFromPcm16Base64(data.delta||'');
      if (Math.random()<0.1) console.debug('[VU] amp', amp);
      updateVu(currentWorkerIdMemo||'', amp);
    }catch(_){ }
    // Ne conditionne pas la lecture audio à currentResponseId : on joue si on n'interrompt pas l'IA
    if (data.delta && window.audioPlayer && !window.isUserSpeaking){ try{ audioPlayer.playBase64Pcm16(data.delta); }catch(_){ } }
  }
  if (t==='response.function_call_arguments.done') handleFunctionCall(data);
}

// Expose
window.connectWebSocket = connectWebSocket;
window.handleRealtimeMessage = handleRealtimeMessage;
