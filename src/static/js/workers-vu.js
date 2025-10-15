/**
 * Workers VU Ring - avatar ring animation driven by AI speech amplitude
 * - Smoothing léger (EMA) + fort effet visuel
 */

const _vuSmooth = Object.create(null); // workerId -> last smoothed amp

function setAISpeaking(on, workerId){
  try{
    const wid = workerId || window.currentCallWorkerId;
    if (!wid) return;
    const avatar = document.querySelector(`#card-${wid} .worker-avatar`);
    if (avatar) avatar.classList.toggle('vu-active', !!on);
  }catch(_){}
}

function updateVu(workerId, amp){
  try{
    const avatar = document.querySelector(`#card-${workerId} .worker-avatar`);
    if (!avatar) return;
    // Smoothing (EMA)
    const prev = _vuSmooth[workerId] ?? 0;
    const alpha = 0.3; // un peu plus réactif
    const smoothed = Math.min(Math.max(prev*(1-alpha) + amp*alpha, 0), 1);
    _vuSmooth[workerId] = smoothed;

    // Effet fort (non-linéaire)
    const gain = Math.sqrt(smoothed); // boost non-linéaire
    const scale = 1 + gain * 6.0; // 1 → 7

    // Couleur
    let color = '#10b981'; // green
    if (gain >= 0.7) color = '#ef4444';
    else if (gain >= 0.35) color = '#f59e0b';

    avatar.style.setProperty('--vu-scale', String(scale));
    avatar.style.setProperty('--vu-color', color);
    avatar.classList.add('vu-active');
  }catch(_){}
}

function resetVu(workerId){
  try{
    const avatar = document.querySelector(`#card-${workerId} .worker-avatar`);
    if (!avatar) return;
    avatar.classList.remove('vu-active');
    avatar.style.removeProperty('--vu-scale');
    avatar.style.removeProperty('--vu-color');
    delete _vuSmooth[workerId];
  }catch(_){}
}

// Helpers amplitude from base64 PCM16LE
function ampFromPcm16Base64(b64){
  try{
    const bin = atob(b64);
    const len = bin.length;
    if (len < 2) return 0;
    let sum = 0; let count = 0;
    for (let i=0;i<len-1;i+=2){
      const lo = bin.charCodeAt(i);
      const hi = bin.charCodeAt(i+1);
      let val = (hi << 8) | lo; if (val & 0x8000) val = val - 0x10000; // signed
      const f = Math.abs(val / 32768);
      sum += f; count++;
    }
    if (count === 0) return 0;
    const avg = sum / count; // average rectified value
    return Math.min(Math.max(avg * 1.8, 0), 1); // boost
  }catch(_){ return 0; }
}

// Expose
window.updateVu = updateVu;
window.resetVu = resetVu;
window.setAISpeaking = setAISpeaking;
window.ampFromPcm16Base64 = ampFromPcm16Base64;
