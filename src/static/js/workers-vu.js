

// === PATCH: verbose VU debug + ring check ===
(function(){
  const state = { ema: {} };

  function colorClassFor(level){
    if (level >= 0.66) return 'vu-red';
    if (level >= 0.33) return 'vu-yellow';
    return 'vu-green';
  }

  function setWorkerLevel(workerId, level){
    const card = document.querySelector(`.worker-card[data-worker-id="${CSS.escape(workerId)}"]`) || document.getElementById(`card-${workerId}`);
    if (!card){ if (window.__DF_DEBUG) console.warn('[VU] card not found for', workerId); return; }
    const ring = card.querySelector('.avatar-ring');
    if (!ring){ if (window.__DF_DEBUG) console.warn('[VU] ring not found in card', workerId, card); return; }

    const clamped = Math.max(0, Math.min(1, Number(level)||0));
    ring.style.setProperty('--level', clamped.toFixed(3));

    card.classList.remove('vu-green','vu-yellow','vu-red');
    card.classList.add(colorClassFor(clamped));

    if (clamped > 0.08) card.classList.add('speaking'); else card.classList.remove('speaking');

    if (window.__DF_DEBUG) {
      console.debug('[VU:set]', { workerId, level: clamped, classes: [...card.classList] });
      // Small visual outline to confirm ring element
      ring.style.outline = '1px solid #22c55e';
      clearTimeout(ring.__dbg);
      ring.__dbg = setTimeout(() => { try { ring.style.outline = ''; } catch(_){} }, 300);
    }
  }

  function updateVu(workerId, amp){
    const key = String(workerId);
    const prev = state.ema[key] ?? 0;
    const alpha = 0.35;
    const smoothed = alpha * amp + (1 - alpha) * prev;
    state.ema[key] = smoothed;

    const level = Math.min(1, Math.pow(smoothed * 3.0, 0.6));
    if (window.__DF_DEBUG) console.debug('[VU:update]', { workerId, amp, smoothed, level });
    setWorkerLevel(workerId, level);
  }

  function resetVu(workerId){
    const key = String(workerId);
    state.ema[key] = 0;
    setWorkerLevel(workerId, 0);
  }

  function setAISpeaking(on){
    try {
      const id = window.currentWorkerIdMemo || window.currentCallWorkerId;
      if (!id) return;
      const card = document.querySelector(`.worker-card[data-worker-id="${CSS.escape(id)}"]`) || document.getElementById(`card-${id}`);
      if (!card) return;
      card.classList.toggle('speaking', !!on);
      if (window.__DF_DEBUG) console.debug('[VU:aiSpeaking]', { id, on });
    } catch(_){ }
  }

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

  window.addEventListener('worker-vu', (e) => {
    const { id, level } = e.detail || {};
    if (id != null) setWorkerLevel(id, Number(level)||0);
  });

  window.WorkersVU = { setWorkerLevel, updateVu, resetVu, ampFromPcm16Base64 };
  window.updateVu = updateVu;
  window.resetVu = resetVu;
  window.setAISpeaking = setAISpeaking;
  window.ampFromPcm16Base64 = ampFromPcm16Base64;
})();
