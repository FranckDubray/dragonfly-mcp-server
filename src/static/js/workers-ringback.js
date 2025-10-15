


/**
 * Workers Ringback - Familiar, pleasant ringback patterns for 2–10s init windows
 * Modes:
 *  - 'double_beep': 440 Hz sine, 0.2 ON, 0.2 OFF, 0.2 ON, 2.0 OFF (cycle ~2.6s)
 *  - 'skype_like' (default): two-tone (~400/450 Hz) with tu-tu-tuu cadence (cycle ~4.0s)
 */

class RingbackTone {
    constructor(options = {}) {
        this.audioCtx = null;
        this.isPlaying = false;
        this.gain = null;
        this.osc1 = null;
        this.osc2 = null;
        this._cycleTimer = null;
        this.mode = options.mode || 'skype_like';
        this.baseGain = options.baseGain ?? 0.18; // mix target; actual output controlled by masterGain
        this.cycleMs = this.mode === 'double_beep' ? 2600 : 4000;
        this.masterGain = null; // external volume control
    }

    setMode(mode){
        if (!['double_beep','skype_like'].includes(mode)) return;
        const wasPlaying = this.isPlaying;
        this.stop();
        this.mode = mode;
        this.cycleMs = this.mode === 'double_beep' ? 2600 : 4000;
        if (wasPlaying) this.start();
    }

    _init() {
        if (this.audioCtx) return;
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        this.audioCtx = new AudioContextClass();
        this.gain = this.audioCtx.createGain();
        this.gain.gain.value = 0.0;
        // master gain to allow shared volume control with slider
        this.masterGain = this.audioCtx.createGain();
        this.masterGain.gain.value = 0.5; // défaut cohérent curseur 50%
        this.gain.connect(this.masterGain);
        this.masterGain.connect(this.audioCtx.destination);
    }

    setVolume(v){
        try{
          if (!this.audioCtx) this._init();
          const vol = Math.max(0, Math.min(1, Number(v)));
          if (this.masterGain) this.masterGain.gain.value = vol;
        }catch(_){ }
    }

    _createOsc1(startAt, freq, type='sine'){
        const o = this.audioCtx.createOscillator();
        o.type = type; o.frequency.setValueAtTime(freq, startAt);
        o.connect(this.gain); o.start(startAt);
        return o;
    }

    _stopOsc(osc, t){ try { if (osc) { osc.stop(t); osc.disconnect(); } } catch(_){} }

    _scheduleCycle(){
        if (this.mode === 'double_beep') return this._scheduleCycleDoubleBeep();
        return this._scheduleCycleSkypeLike();
    }

    _scheduleCycleDoubleBeep(){
        const ctx = this.audioCtx; if (!ctx) return;
        const now = ctx.currentTime + 0.01;
        const g = this.gain.gain;
        const vol = this.baseGain;
        const fade = 0.01;
        this.osc1 = this._createOsc1(now, 440, 'sine');
        g.cancelScheduledValues(now);
        g.setValueAtTime(0.0, now);
        // Beep #1 (0.0–0.2)
        g.linearRampToValueAtTime(vol, now + fade);
        g.setValueAtTime(vol, now + 0.2 - fade);
        g.linearRampToValueAtTime(0.0, now + 0.2);
        // Gap (0.2–0.4)
        g.setValueAtTime(0.0, now + 0.4);
        // Beep #2 (0.4–0.6)
        g.linearRampToValueAtTime(vol, now + 0.4 + fade);
        g.setValueAtTime(vol, now + 0.6 - fade);
        g.linearRampToValueAtTime(0.0, now + 0.6);
        // Rest to end (0.6–2.6)
        g.setValueAtTime(0.0, now + 2.6);
        this._stopOsc(this.osc1, now + 2.6 + 0.02); this.osc1 = null;
        this._cycleTimer = setTimeout(() => { if (!this.isPlaying) return; try { this._scheduleCycle(); } catch(_){} }, this.cycleMs - 5);
    }

    _scheduleCycleSkypeLike(){
        const ctx = this.audioCtx; if (!ctx) return;
        const now = ctx.currentTime + 0.01;
        const g = this.gain.gain;
        const vol = this.baseGain;
        const fade = 0.015;
        const o1 = this._createOsc1(now, 400);
        const o2 = this._createOsc1(now, 450);
        this.osc1 = o1; this.osc2 = o2;
        g.cancelScheduledValues(now);
        g.setValueAtTime(0.0, now);
        // ON 0.0–0.4
        g.linearRampToValueAtTime(vol, now + fade);
        g.setValueAtTime(vol, now + 0.4 - fade);
        g.linearRampToValueAtTime(0.0, now + 0.4);
        // Gap 0.4–0.6
        g.setValueAtTime(0.0, now + 0.6);
        // ON 0.6–1.0
        g.linearRampToValueAtTime(vol, now + 0.6 + fade);
        g.setValueAtTime(vol, now + 1.0 - fade);
        g.linearRampToValueAtTime(0.0, now + 1.0);
        // ON 1.0–1.4 (long)
        g.linearRampToValueAtTime(vol, now + 1.0 + fade);
        g.setValueAtTime(vol, now + 1.4 - fade);
        g.linearRampToValueAtTime(0.0, now + 1.4);
        // Gap 1.4–1.6
        g.setValueAtTime(0.0, now + 1.6);
        // ON 1.6–2.0
        g.linearRampToValueAtTime(vol, now + 1.6 + fade);
        g.setValueAtTime(vol, now + 2.0 - fade);
        g.linearRampToValueAtTime(0.0, now + 2.0);
        // OFF 2.0–4.0
        g.setValueAtTime(0.0, now + 4.0);
        this._stopOsc(this.osc1, now + 4.02);
        this._stopOsc(this.osc2, now + 4.02);
        this.osc1 = null; this.osc2 = null;
        this._cycleTimer = setTimeout(() => { if (!this.isPlaying) return; try { this._scheduleCycle(); } catch(_){} }, this.cycleMs - 5);
    }

    async start() {
        if (this.isPlaying) return;
        this._init();
        try { if (this.audioCtx.state === 'suspended') await this.audioCtx.resume(); } catch(_){ }
        this.isPlaying = true;
        try { this._scheduleCycle(); } catch(e){ console.warn('Ringback schedule error:', e); }
    }

    stop() {
        if (!this.isPlaying) return;
        this.isPlaying = false;
        try { if (this._cycleTimer) clearTimeout(this._cycleTimer); this._cycleTimer = null; } catch(_){ }
        try { const t = (this.audioCtx?.currentTime||0) + 0.01; if (this.gain) this.gain.gain.cancelScheduledValues(t); } catch(_){ }
        try { this._stopOsc(this.osc1, (this.audioCtx?.currentTime||0) + 0.02); } catch(_){ }
        try { this._stopOsc(this.osc2, (this.audioCtx?.currentTime||0) + 0.02); } catch(_){ }
        this.osc1 = null; this.osc2 = null;
    }
}

// Global instance, default to skype_like; share volume control via setVolume()
const ringbackTone = new RingbackTone({ mode: 'skype_like', baseGain: 0.18 });

 
 
 
 
 