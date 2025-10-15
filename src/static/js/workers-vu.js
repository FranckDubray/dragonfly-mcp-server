// Workers VU Ring (visible green/yellow/red around avatar) + legacy compat
(function(){
  const state = {
    ema: {}, // per workerId smoothing
  };

  function colorClassFor(level){
    if (level >= 0.66) return 'vu-red';
    if (level >= 0.33) return 'vu-yellow';
    return 'vu-green';
  }

  function setWorkerLevel(workerId, level){
    const card = document.querySelector(`.worker-card[data-worker-id="${CSS.escape(workerId)}"]`) || document.getElementById(`card-${workerId}`);
    if (!card) return;
    const ring = card.querySelector('.avatar-ring');
    if (!ring) return;

    const clamped = Math.max(0, Math.min(1, Number(level)||0));
    ring.style.setProperty('--level', clamped.toFixed(3));

    // Color classes
    card.classList.remove('vu-green','vu-yellow','vu-red');
    card.classList.add(colorClassFor(clamped));

    // Speaking pulse when level is audible
    if (clamped > 0.12) card.classList.add('speaking'); else card.classList.remove('speaking');
  }

  function updateVu(workerId, amp){
    // Smooth with EMA per worker
    const key = String(workerId);
    const prev = state.ema[key] ?? 0;
    const alpha = 0.35; // responsiveness
    const smoothed = alpha * amp + (1 - alpha) * prev;
    state.ema[key] = smoothed;

    // Non-linear boost for visibility
    const level = Math.min(1, Math.pow(smoothed * 3.0, 0.6));
    setWorkerLevel(workerId, level);
  }

  function resetVu(workerId){
    const key = String(workerId);
    state.ema[key] = 0;
    setWorkerLevel(workerId, 0);
  }

  function setAISpeaking(on){
    // Global toggle (used on start/stop of AI audio)
    try {
      const id = window.currentWorkerIdMemo || window.currentCallWorkerId;
      if (!id) return;
      const card = document.querySelector(`.worker-card[data-worker-id="${CSS.escape(id)}"]`) || document.getElementById(`card-${id}`);
      if (!card) return;
      card.classList.toggle('speaking', !!on);
    } catch(_){}
  }

  // Decode base64 PCM16 mono and compute RMS amplitude in [0..1]
  function ampFromPcm16Base64(b64){
    try{
      if (!b64) return 0;
      const bin = atob(b64);
      const len = bin.length;
      if (len < 4) return 0;
      const bytes = new Uint8Array(len);
      for (let i=0;i<len;i++) bytes[i] = bin.charCodeAt(i);
      const dv = new DataView(bytes.buffer);
      const samples = len >> 1;
      let sum = 0;
      for (let i=0;i<samples;i++){
        const s = dv.getInt16(i*2, true) / 32768;
        sum += s * s;
      }
      const rms = Math.sqrt(sum / Math.max(1, samples));
      return Math.max(0, Math.min(1, rms));
    }catch(_){ return 0; }
  }

  // Event bridge (optional)
  window.addEventListener('worker-vu', (e) => {
    const { id, level } = e.detail || {};
    if (id != null) setWorkerLevel(id, Number(level)||0);
  });

  // Expose modern API
  window.WorkersVU = { setWorkerLevel, updateVu, resetVu, ampFromPcm16Base64 };
  // Backward compat for session-ws
  window.updateVu = updateVu;
  window.resetVu = resetVu;
  window.setAISpeaking = setAISpeaking;
  window.ampFromPcm16Base64 = ampFromPcm16Base64;
})();
