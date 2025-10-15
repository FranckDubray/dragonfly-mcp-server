/**
 * Workers Ringback - Son de numérotation simple
 * Beep téléphone classique (pas le truc bizarre Skype)
 */

class RingbackTone {
    constructor() {
        this.audioCtx = null;
        this.isPlaying = false;
        this.osc = null;
        this.gainNode = null;
        this.intervalId = null;
    }
    
    _init() {
        if (this.audioCtx) return;
        
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        this.audioCtx = new AudioContextClass();
        
        console.log('🔊 Ringback tone initialized');
    }
    
    start() {
        if (this.isPlaying) return;
        
        this._init();
        
        // Resume context si suspendu
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume().catch(() => {});
        }
        
        this.isPlaying = true;
        
        // Beep simple : 1 seconde ON, 2 secondes OFF
        this._playBeep();
        this.intervalId = setInterval(() => {
            if (this.isPlaying) {
                this._playBeep();
            }
        }, 3000); // Répéter toutes les 3 secondes
        
        console.log('📞 Ringback tone started (simple beep)');
    }
    
    _playBeep() {
        if (!this.audioCtx || !this.isPlaying) return;
        
        try {
            // Créer oscillateur pour ce beep
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            
            osc.frequency.value = 440; // La 440Hz (simple et clair)
            osc.type = 'sine';
            
            osc.connect(gain);
            gain.connect(this.audioCtx.destination);
            
            const now = this.audioCtx.currentTime;
            
            // Fade in/out pour éviter clicks
            gain.gain.setValueAtTime(0, now);
            gain.gain.linearRampToValueAtTime(0.1, now + 0.05);
            gain.gain.setValueAtTime(0.1, now + 0.8);
            gain.gain.linearRampToValueAtTime(0, now + 0.85);
            
            osc.start(now);
            osc.stop(now + 1);
            
            // Cleanup
            osc.onended = () => {
                try {
                    osc.disconnect();
                    gain.disconnect();
                } catch (_) {}
            };
        } catch (e) {
            console.warn('Beep play error:', e);
        }
    }
    
    stop() {
        if (!this.isPlaying) return;
        
        this.isPlaying = false;
        
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        
        console.log('🔇 Ringback tone stopped');
    }
}

// Instance globale
const ringbackTone = new RingbackTone();
