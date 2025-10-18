














/**
 * Workers Audio - lecteur PCM16 avec contrôle de volume et arrêt immédiat
 */

(function(){
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  let ctx = null;
  let gain = null;

  function ensureContext() {
    if (!ctx) {
      ctx = new AudioContextClass({ sampleRate: 24000 });
      gain = ctx.createGain();
      gain.gain.value = 0.5; // défaut 50%
      gain.connect(ctx.destination);
      if (window.audioPlayer) window.audioPlayer.queueTime = ctx.currentTime;
    }
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});
    return ctx;
  }

  function base64ToBytes(b64) {
    const bin = atob(b64); const len = bin.length; const out = new Uint8Array(len);
    for (let i=0;i<len;i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  window.audioPlayer = {
    queueTime: 0,
    activeSources: [],
    _preDuckVolume: null,
    _ducking: false,

    setVolume(v) {
      ensureContext();
      const vol = Math.max(0, Math.min(1, Number(v)));
      gain.gain.value = vol;
      if (window.__DF_DEBUG) console.log('[AUDIO:setVolume]', vol);
    },

    beginDuck(factor = 0.6) {
      try{
        ensureContext();
        if (!this._ducking){
          this._preDuckVolume = gain.gain.value;
          const f = Math.max(0, Math.min(1, Number(factor)));
          gain.gain.value = Math.max(0, Math.min(1, this._preDuckVolume * f));
          this._ducking = true;
          if (window.__DF_DEBUG) console.log('[AUDIO:duck start]', { from: this._preDuckVolume, to: gain.gain.value });
        }
      }catch(_){ }
    },

    endDuck() {
      try{
        if (this._ducking){
          const restore = (typeof this._preDuckVolume === 'number') ? this._preDuckVolume : gain.gain.value;
          gain.gain.value = Math.max(0, Math.min(1, restore));
          if (window.__DF_DEBUG) console.log('[AUDIO:duck stop]', { to: gain.gain.value });
          this._preDuckVolume = null;
          this._ducking = false;
        }
      }catch(_){ }
    },

    playBase64Pcm16(b64) {
      if (!b64) return;
      ensureContext();

      const bytes = base64ToBytes(b64);
      const samples = bytes.length >> 1;
      const float32 = new Float32Array(samples);
      const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
      for (let i = 0; i < samples; i++) {
        const s = dv.getInt16(i*2, true);
        float32[i] = s / 32768;
      }
      const buf = ctx.createBuffer(1, float32.length, 24000);
      buf.copyToChannel(float32, 0, 0);

      const src = ctx.createBufferSource();
      src.buffer = buf;
      src.connect(gain);

      this.activeSources.push(src);
      src.onended = () => {
        const i = this.activeSources.indexOf(src);
        if (i > -1) this.activeSources.splice(i, 1);
      };

      const now = ctx.currentTime;
      const startAt = Math.max(now, this.queueTime || now);
      src.start(startAt);
      this.queueTime = startAt + buf.duration;
    },

    stopAll() {
      this.activeSources.forEach(s => { try { s.stop(0); s.disconnect(); } catch(_){} });
      this.activeSources = [];
      if (ctx) this.queueTime = ctx.currentTime;
    }
  };

  window.setVolume = function(v){
    try { window.audioPlayer.setVolume(v); } catch(_){}
    try { window.ringbackTone?.setVolume?.(v); } catch(_){}
  }
  window.unlockAudio = function(){ try { ensureContext(); } catch(_){} }
  window.getAudioContext = function(){ try { return ensureContext(); } catch(_){ return null; } }
})();

 
 
 
 
 
 
 
 
 
 
 
 
