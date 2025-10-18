














/**
 * Workers Session - Audio & VAD client (AudioWorklet-based, with debug on outbound events)
 */

let audioContext = null;
let workletNode = null;
let sourceNode = null;
let isSpeaking = false;
let silenceFrames = 0;
// Hysteresis & noise gate (conservateurs)
const SILENCE_THRESHOLD_ON = 0.035;
const SILENCE_THRESHOLD_OFF = 0.020;
const MIN_SPEAK_FRAMES = 6;
const SILENCE_FRAMES_NEEDED = 10;
let speakFrames = 0;
let speechStartTs = 0;

// NEW: barge-in hold window (~300ms) to avoid cutting assistant on very short noises
const VAD_HOLD_MS = 300; // confirmation window
const DUCK_FACTOR = 0.6; // volume reduction during hold
let holdMs = 0;
let holdActive = false;

// Debug throttling for upstream appends
const __vadDebug = { lastAppendLogTs: 0, appendCount: 0, appendedBytes: 0 };

async function ensureAudioContext(){
  if (audioContext) return audioContext;
  const Ctx = window.AudioContext || window.webkitAudioContext;
  audioContext = new Ctx({ sampleRate: 24000 });
  // Load worklet once
  try {
    await audioContext.audioWorklet.addModule('/static/js/vad-worklet.js');
  } catch (e) {
    console.warn('[VAD] Failed to load worklet, fallback to ScriptProcessor', e);
    audioContext = null; // Signal fallback
  }
  return audioContext;
}

async function startRecording(){
  if (!ws || ws.readyState!==WebSocket.OPEN) return;
  let ctx = await ensureAudioContext();
  let useFallback = false;
  if (!ctx) { // worklet failed, fallback to ScriptProcessor
    const Ctx = window.AudioContext || window.webkitAudioContext;
    ctx = new Ctx({ sampleRate: 24000 });
    useFallback = true;
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio:{ channelCount:1, echoCancellation:true, noiseSuppression:true, autoGainControl:true } });
  const src = ctx.createMediaStreamSource(stream);
  sourceNode = src;

  if (!useFallback){
    // Worklet path
    workletNode = new AudioWorkletNode(ctx, 'vad-processor', { numberOfInputs:1, numberOfOutputs:0 });
    src.connect(workletNode);

    // Accumulate and process frames from worklet
    const frameSize = 2048; // ~85ms @24k
    let acc = new Float32Array(0);
    workletNode.port.onmessage = (ev) => {
      const chunk = ev.data; // Float32Array (render quantum ~128)
      // Concatenate into acc
      const merged = new Float32Array(acc.length + chunk.length);
      merged.set(acc, 0); merged.set(chunk, acc.length); acc = merged;
      if (acc.length >= frameSize){
        processVadFrame(acc.subarray(0, frameSize));
        acc = acc.subarray(frameSize);
      }
    };
  } else {
    // Fallback ScriptProcessor (deprecated but safe)
    const bufferSize = 2048;
    const proc = ctx.createScriptProcessor(bufferSize,1,1);
    proc.onaudioprocess = (e)=>{ processVadFrame(e.inputBuffer.getChannelData(0)); };
    src.connect(proc); proc.connect(ctx.destination);
    workletNode = proc;
  }
}

function processVadFrame(input){
  // RMS
  let sum=0; for(let i=0;i<input.length;i++){ sum += input[i]*input[i]; }
  const rms = Math.sqrt(sum/input.length);
  const frameMs = (input.length / 24000) * 1000;

  // HOLD window logic: require ~300ms sustained above threshold before confirming barge-in
  if (!isSpeaking){
    if (rms > SILENCE_THRESHOLD_ON){
      // start/advance hold
      holdActive = true;
      holdMs += frameMs;
      try{ audioPlayer?.beginDuck?.(DUCK_FACTOR); }catch(_){ }
      // Also keep legacy hysteresis counter for diagnostics (optional)
      speakFrames++;
      if (holdMs >= VAD_HOLD_MS){
        // CONFIRM user speaking
        isSpeaking = true; window.isUserSpeaking = true; speakFrames=0;
        speechStartTs = performance.now();
        if (window.__DF_DEBUG) console.log('[VAD:speaking_confirmed]', { rms: +rms.toFixed(4), holdMs: Math.round(holdMs) });
        // HARD CUT IA seulement si hors fenêtre de grâce
        try{
          if (currentResponseId && ws?.readyState===WebSocket.OPEN){
            if (window.aiGraceUntil && Date.now() < window.aiGraceUntil){
              if (window.__DF_DEBUG) console.log('[VAD] cancel suppressed (aiGraceUntil)');
            } else {
              if (window.__DF_DEBUG) console.log('[VAD:send response.cancel]', { response_id: currentResponseId });
              ws.send(JSON.stringify({type:'response.cancel', response_id: currentResponseId}));
            }
          }
        }catch(_){ }
        // Stop assistant audio only after confirmation (avoid cutting on short noise)
        try{ audioPlayer?.stopAll?.(); }catch(_){ }
      }
    } else if (rms < SILENCE_THRESHOLD_OFF) {
      // noise fell below off → if hold not confirmed, treat as short noise and reset
      if (holdActive && holdMs < VAD_HOLD_MS){
        // short noise: cancel duck and reset hold, do not cancel assistant
        try{ audioPlayer?.endDuck?.(); }catch(_){ }
        holdMs = 0; holdActive = false; speakFrames = 0;
        if (window.__DF_DEBUG) console.log('[VAD:noise_ignored]', { rms: +rms.toFixed(4) });
      }
      // maintain legacy counters
      silenceFrames++;
      if (silenceFrames > SILENCE_FRAMES_NEEDED){ silenceFrames=0; }
    }
  } else {
    // already speaking: look for end of speaking
    if (rms < SILENCE_THRESHOLD_OFF){
      silenceFrames++;
      if (silenceFrames > SILENCE_FRAMES_NEEDED){
        isSpeaking=false; window.isUserSpeaking=false; silenceFrames=0;
        try{
          if (speechStartTs){ window.userLastSpeechMs = Math.max(0, performance.now() - speechStartTs); }
        }catch(_){ }
        if (window.__DF_DEBUG) console.log('[VAD:speaking_stop]', { rms: +rms.toFixed(4), duration_ms: Math.round(window.userLastSpeechMs||0) });
        speechStartTs = 0;
        // reset hold/duck states
        try{ audioPlayer?.endDuck?.(); }catch(_){ }
        holdMs = 0; holdActive = false;
      }
    } else {
      silenceFrames=0;
    }
  }

  // Uplink audio to server in ~50ms chunks
  // Downsample already at 24k; just slice into 1200 samples (~50ms)
  const chunkSize = 1200; // 50ms @24k
  if (!window.__vadUplinkBuf) window.__vadUplinkBuf = new Float32Array(0);
  const prev = window.__vadUplinkBuf;
  const merged = new Float32Array(prev.length + input.length);
  merged.set(prev,0); merged.set(input, prev.length); window.__vadUplinkBuf = merged;

  while (window.__vadUplinkBuf.length >= chunkSize){
    const toSend = window.__vadUplinkBuf.subarray(0, chunkSize);
    window.__vadUplinkBuf = window.__vadUplinkBuf.subarray(chunkSize);
    const pcm = floatToPCM16(toSend);
    const b64 = base64FromBytes(pcm);
    ws?.send(JSON.stringify({type:'input_audio_buffer.append', audio: b64}));
    if (window.__DF_DEBUG){
      try{
        __vadDebug.appendCount++; __vadDebug.appendedBytes += pcm.length;
        const now = performance.now();
        if (!__vadDebug.lastAppendLogTs || now - __vadDebug.lastAppendLogTs >= 500){
          console.log('[VAD:append]', { count: __vadDebug.appendCount, bytes: __vadDebug.appendedBytes });
          __vadDebug.lastAppendLogTs = now; __vadDebug.appendCount=0; __vadDebug.appendedBytes=0;
        }
      }catch(_){ }
    }
  }
}

function stopRecording(){
  try{ workletNode?.port?.close?.(); }catch(_){ }
  try{ workletNode?.disconnect?.(); }catch(_){ }
  try{ sourceNode?.disconnect?.(); }catch(_){ }
  try{ if (audioContext && audioContext.state!=='closed'){ audioContext.close(); } }catch(_){ }
  try{ localStream?.getTracks().forEach(t=>t.stop()); }catch(_){ }
  workletNode=null; sourceNode=null; audioContext=null; localStream=null;
}

function base64FromBytes(bytes){ let bin=''; const chunk=0x8000; for (let i=0;i<bytes.length;i+=chunk){ const sub=bytes.subarray(i,i+chunk); bin += String.fromCharCode.apply(null, sub); } return btoa(bin); }
function floatToPCM16(float32){ const dv = new DataView(new ArrayBuffer(float32.length*2)); let off=0; for(let i=0;i<float32.length;i++,off+=2){ let s=Math.max(-1,Math.min(1,float32[i])); dv.setInt16(off, s<0 ? s*0x8000 : s*0x7FFF, true);} return new Uint8Array(dv.buffer); }

// Expose
window.startRecording = startRecording;
window.stopRecording = stopRecording;

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
