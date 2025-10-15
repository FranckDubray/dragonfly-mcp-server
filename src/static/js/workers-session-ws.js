/**
 * Workers Session - WebSocket & events
 */

function startAutoGreeting(){ autoGreetingTimer = setTimeout(()=>{ if (!userHasSpoken && sessionActive) sendResponseCreateSafe('auto-greeting'); }, 3000); }
function cancelAutoGreeting(){ if (autoGreetingTimer){ clearTimeout(autoGreetingTimer); autoGreetingTimer = null; } }

async function connectWebSocket(url){
  return new Promise((resolve, reject)=>{
    try{
      ws = new WebSocket(url);
      ws.onopen = ()=>{ try{ ringbackTone?.stop?.(); }catch(_){ }
        // Pousser tools/instructions immédiatement via session.update (sécurise l'activation tool)
        try{
          if (Array.isArray(currentWorkerConfig?.tools) && currentWorkerConfig.tools.length){
            ws.send(JSON.stringify({ type:'session.update', session:{ type:'realtime', instructions: currentWorkerConfig.instructions||'', tools: currentWorkerConfig.tools, tool_choice: 'auto' } }));
          }
        }catch(e){ console.warn('[REALTIME] session.update failed to send on open:', e?.message||e); }
        resolve(); };
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
    // Si l'erreur est liée à session.update type manquant/invalide, renvoyer avec type
    if (/session\.type/i.test(msg)){
      try{
        ws.send(JSON.stringify({ type:'session.update', session:{ type:'realtime', instructions: currentWorkerConfig.instructions||'', tools: currentWorkerConfig.tools||[], tool_choice: 'auto' } }));
      }catch(e){ console.warn('[REALTIME] retry session.update failed:', e?.message||e); }
    }
  }
  if (t==='response.created'){
    currentResponseId = data.response?.id||null;
    responseCreatePending = false;
    assistantBuffer = ""; // reset pour la nouvelle réponse
  }
  if (t==='response.done' || t==='response.cancelled'){
    currentResponseId = null; window.isUserSpeaking=false; try{ updateVu(currentWorkerIdMemo||'', 0); resetVu(currentWorkerIdMemo||''); setAISpeaking(false); }catch(_){ }
  }

  if (t==='input_audio_buffer.speech_started'){
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
    const finalText = data.transcript || assistantBuffer || '';
    miniAppend('assistant', finalText);
    inlineAppend('assistant', finalText); // no-op
    assistantBuffer = "";
  }
  if (t==='response.output_audio.delta'){
    try{ ringbackTone?.stop?.(); gotFirstAIAudio = true; setAISpeaking(true); }catch(_){ }
    try{
      const amp = ampFromPcm16Base64(data.delta||'');
      if (Math.random()<0.1) console.debug('[VU] amp', amp);
      updateVu(currentWorkerIdMemo||'', amp);
    }catch(_){ }
    if (currentResponseId && data.delta && window.audioPlayer && !window.isUserSpeaking){ try{ audioPlayer.playBase64Pcm16(data.delta); }catch(_){ } }
  }
  if (t==='response.function_call_arguments.done') handleFunctionCall(data);
}

// Expose
window.connectWebSocket = connectWebSocket;
window.handleRealtimeMessage = handleRealtimeMessage;
