
/* Simple, audible ringback routed through audioPlayer (no recursion, no global setVolume call) */
(function(){
  function genSinePcm16_24k(freqHz, durMs, vol){
    const sr = 24000;
    const samples = Math.max(1, Math.floor(sr * (durMs/1000)));
    const out = new Int16Array(samples);
    const twoPiF = 2*Math.PI*freqHz;
    const amp = Math.max(0, Math.min(1, Number(vol||0.6))) * 0x7FFF;
    for (let i=0;i<samples;i++){
      const t = i / sr;
      out[i] = Math.max(-32768, Math.min(32767, Math.round(Math.sin(twoPiF*t) * amp)));
    }
    const bytes = new Uint8Array(out.buffer);
    let bin=''; const chunk=0x8000; for (let i=0;i<bytes.length;i+=chunk){ bin += String.fromCharCode.apply(null, bytes.subarray(i,i+chunk)); }
    return btoa(bin);
  }

  class SimpleRingback {
    constructor(){
      this.isPlaying = false;
      this._timer = null;
      this.volume = 0.7; // un peu plus fort
      this.__startTs = 0;
      this.mode = 'pcm24k';
    }
    _playBurst(){
      try{
        if (!window.audioPlayer) return;
        // 440 Hz, 500ms ON (plus neutre/agréable)
        const b64 = genSinePcm16_24k(440, 500, this.volume);
        audioPlayer.playBase64Pcm16(b64);
      }catch(e){ if (window.__DF_DEBUG) console.warn('[RINGBACK] play burst failed', e); }
    }
    setVolume(v){
      const vol = Math.max(0, Math.min(1, Number(v)));
      this.volume = vol; // ne PAS appeler window.setVolume ici (évite récursion)
      if (window.__DF_DEBUG) console.log('[RINGBACK] setVolume ->', vol);
    }
    async start(){
      if (this.isPlaying) return;
      this.isPlaying = true;
      try { this.__startTs = (performance && performance.now)? performance.now(): Date.now(); } catch(_){ this.__startTs = Date.now(); }
      if (window.__DF_DEBUG) console.log('[RINGBACK] start(simple) t0=', this.__startTs);
      this._playBurst();
      clearInterval(this._timer);
      // 500ms ON + 500ms OFF => une impulsion toutes les 1000ms
      this._timer = setInterval(()=>{ if (!this.isPlaying) return; this._playBurst(); }, 1000);
    }
    stop(force){
      try{
        const MIN = 2000; const now = (performance&&performance.now)?performance.now():Date.now();
        const elapsed = this.__startTs ? (now - this.__startTs) : MIN;
        if (!force && elapsed < MIN){
          const wait = Math.max(0, MIN - elapsed);
          if (window.__DF_DEBUG) console.log('[RINGBACK] stop deferred(simple)', { elapsed: Math.round(elapsed), wait });
          clearTimeout(this.__stopTimer);
          this.__stopTimer = setTimeout(()=> this.stop(true), wait);
          return;
        }
      }catch(_){ }
      if (!this.isPlaying) return;
      this.isPlaying = false;
      clearInterval(this._timer); this._timer = null;
      if (window.__DF_DEBUG) console.log('[RINGBACK] stop(simple)');
    }
  }

  // Remplace global ringbackTone si nécessaire (évite double-définition)
  try{ window.ringbackTone = new SimpleRingback(); }catch(e){ console.warn('[RINGBACK] simple init failed', e); }
})();
