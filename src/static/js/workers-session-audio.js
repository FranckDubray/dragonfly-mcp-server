
/**
 * Workers Session - Audio & VAD client minimal (immediate cut on user speech)
 */

let audioContext = null;
let sourceNode = null;
let processorNode = null;
let isSpeaking = false;
let silenceFrames = 0;
const SILENCE_THRESHOLD = 0.01; // RMS threshold
const SILENCE_FRAMES_NEEDED = 4; // ~4*128/24k ≈ 21ms to release speaking

async function startRecording(){
  if (!ws || ws.readyState!==WebSocket.OPEN) return;
  localStream = await navigator.mediaDevices.getUserMedia({ audio:{ channelCount:1, echoCancellation:true, noiseSuppression:true, autoGainControl:true } });
  const Ctx = window.AudioContext || window.webkitAudioContext;
  audioContext = new Ctx({sampleRate:24000});
  sourceNode = audioContext.createMediaStreamSource(localStream);
  const bufferSize = 2048; // smaller buffer for faster detection
  processorNode = audioContext.createScriptProcessor(bufferSize,1,1);

  let pcmByteBuffer = [];
  processorNode.onaudioprocess = (e)=>{
    if (micMuted) return;
    const input = e.inputBuffer.getChannelData(0);
    let sum=0; for(let i=0;i<input.length;i++){ sum += input[i]*input[i]; }
    const rms = Math.sqrt(sum/input.length);

    // Fast attack: as soon as RMS crosses threshold => user speaking
    if (rms>SILENCE_THRESHOLD){
      if (!isSpeaking){
        isSpeaking=true; window.isUserSpeaking=true;
        // HARD CUT: stop all AI audio immediately & cancel active response
        try{ audioPlayer?.stopAll?.(); }catch(_){ }
        try{ if (currentResponseId && ws?.readyState===WebSocket.OPEN){ ws.send(JSON.stringify({type:'response.cancel', response_id: currentResponseId})); } }catch(_){ }
      }
      silenceFrames=0;
    } else {
      silenceFrames++;
      if (silenceFrames> SILENCE_FRAMES_NEEDED){ isSpeaking=false; window.isUserSpeaking=false; }
    }

    // Skip sending if not speaking (and stabilized silence)
    if (!isSpeaking && silenceFrames> SILENCE_FRAMES_NEEDED) return;

    // Downsample to 24kHz PCM16 in small chunks for low latency
    const inRate = audioContext.sampleRate||48000; const down = downsampleBuffer(input, inRate, 24000);
    const pcm = floatToPCM16(down); pcmByteBuffer.push(pcm);
    const total = pcmByteBuffer.reduce((a,b)=>a+b.length,0);
    if (total>=2400){ // ~50ms at 24k mono
      const merged = mergeUint8(pcmByteBuffer); pcmByteBuffer=[];
      ws?.send(JSON.stringify({type:'input_audio_buffer.append', audio: base64FromBytes(merged)}));
    }
  };
  sourceNode.connect(processorNode); processorNode.connect(audioContext.destination);
}

function stopRecording(){
  try{ if (processorNode){ processorNode.disconnect(); processorNode.onaudioprocess=null; } }catch(_){ }
  try{ if (sourceNode){ sourceNode.disconnect(); } }catch(_){ }
  try{ if (audioContext && audioContext.state!=='closed'){ audioContext.close(); } }catch(_){ }
  try{ localStream?.getTracks().forEach(t=>t.stop()); }catch(_){ }
  processorNode=null; sourceNode=null; audioContext=null; localStream=null;
}

function mergeUint8(arrays){ const total = arrays.reduce((a,b)=>a+b.length,0); const out = new Uint8Array(total); let off=0; for(const a of arrays){ out.set(a,off); off+=a.length; } return out; }
function base64FromBytes(bytes){ let bin=''; const chunk=0x8000; for (let i=0;i<bytes.length;i+=chunk){ const sub=bytes.subarray(i,i+chunk); bin += String.fromCharCode.apply(null, sub); } return btoa(bin); }
function floatToPCM16(float32){ const dv = new DataView(new ArrayBuffer(float32.length*2)); let off=0; for(let i=0;i<float32.length;i++,off+=2){ let s=Math.max(-1,Math.min(1,float32[i])); dv.setInt16(off, s<0 ? s*0x8000 : s*0x7FFF, true);} return new Uint8Array(dv.buffer); }
function downsampleBuffer(buffer,inRate,outRate){ if(outRate===inRate) return buffer; const ratio=inRate/outRate; const newLen=Math.round(buffer.length/ratio); const res=new Float32Array(newLen); let offRes=0,offBuf=0; while(offRes<res.length){ const nextOff=Math.round((offRes+1)*ratio); let acc=0,cnt=0; for(let i=offBuf;i<nextOff && i<buffer.length;i++){ acc+=buffer[i]; cnt++; } res[offRes] = cnt>0 ? (acc/cnt):0; offRes++; offBuf=nextOff; } return res; }

// Expose
window.startRecording = startRecording;
window.stopRecording = stopRecording;
