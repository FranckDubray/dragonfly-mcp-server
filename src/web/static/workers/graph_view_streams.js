













































import { startObservePoll } from './observe_poll.js';
import { api } from './api.js';
import { ReplayController } from './replay_driver.js';

export class GraphViewStreams{
  constructor(core, events){ this.core=core; this.events=events; this.mode='observe'; this._fallbackPollStop=null; this._sseAbort=null; this._replay=null; }
  setActive(){
    const kind = this.core.currentKind;
    document.querySelectorAll('.graph-toolbar .btn[data-act]').forEach(b=> b.classList.remove('active'));
    const btn = document.querySelector(`.graph-toolbar .btn[data-act="${kind}"]`);
    if (btn) btn.classList.add('active');
    const mo = document.querySelector(`.graph-toolbar .btn[data-act="mode-${this.mode}"]`);
    if (mo) mo.classList.add('active');
  }
  // ===== Observe (SSE preferred + poll fallback) =====
  async _startSSE(){
    try{
      const url = new URL('/workers/api/observe/stream', location.origin);
      url.searchParams.set('worker', this.core.worker);
      url.searchParams.set('timeout_sec', '30');
      url.searchParams.set('max_events', '200');
      const ctrl = new AbortController(); this._sseAbort = ctrl;
      const r = await fetch(url.toString(), { signal: ctrl.signal });
      if (!r.ok || !r.body){ throw 0; }
      const reader = r.body.getReader(); const dec = new TextDecoder(); let buf='';
      while(true){
        const {value, done} = await reader.read();
        if (done) break;
        buf += dec.decode(value, {stream:true});
        let idx;
        while((idx=buf.indexOf('\n'))>=0){
          const line = buf.slice(0,idx); buf = buf.slice(idx+1);
          if(!line.trim()) continue;
          try{
            const ev = JSON.parse(line);
            const ch = String(ev?.chunk_type||'');
            if (ch==='terminal' || ch==='status' && ['completed','failed','canceled'].includes(String(ev?.phase||'').toLowerCase())){
              this._onTerminal();
            }
            if (ev) this.events.handleEvent(ev);
          }catch{}
        }
      }
    }catch{
      // fallback handled by startObserve()
    }
  }
  _onTerminal(){ setTimeout(async ()=>{ if (this.mode==='observe') { 
      try{
        const st = await api.status(this.core.worker);
        const phase = String(st.phase || st.status || '').toLowerCase();
        if (phase === 'failed'){
          const { openWorkerErrorModal } = await import('./error_modal.js');
          openWorkerErrorModal(this.core.worker, {
            phase: st.phase || st.status,
            heartbeat: st.heartbeat,
            last_error: st.last_error || (st.error && st.error.message) || '',
            io: { in: st.last_call || {}, out_preview: st.last_result_preview || '' }
          });
        }
      }catch{}
      this.stopObserve(); // STOP completely; user can restart observe if needed
      try{ window.dispatchEvent(new CustomEvent('workers:runsRefresh', {detail:{ worker: this.core.worker }})); }catch{}
    } }, 400); }
  startObserve(){
    if (this._fallbackPollStop || this._sseAbort) return;
    // Stop replay if any
    this.stopReplay();
    console.log('[GV-STREAMS] startObserve for worker=', this.core.worker);
    // Try SSE observe stream first (NDJSON). If it ends, _onTerminal will not auto-restart.
    this._startSSE();
    // Also start poll as a safety net if SSE not supported/blocked.
    this._fallbackPollStop = startObservePoll(this.core.worker, evt=>this.events.handleEvent(evt), ()=>this._onTerminal());
    this.mode='observe'; this.setActive();
  }
  stopObserve(){
    if (this._fallbackPollStop){ try{ this._fallbackPollStop(); }catch{} this._fallbackPollStop=null; }
    if (this._sseAbort){ try{ this._sseAbort.abort(); }catch{} this._sseAbort=null; }
  }

  // ===== Debug stream (SSE only) =====
  async startDebugStream(){
    // Stop any observe streams/polls first and replay
    this.stopObserve();
    this.stopReplay();
    if (this._sseAbort) return; // already running a SSE session
    this.mode='debug-stream'; this.setActive();
    try{
      const url = new URL('/workers/api/debug/stream', location.origin);
      url.searchParams.set('worker', this.core.worker);
      url.searchParams.set('timeout_sec', '30');
      url.searchParams.set('max_events', '200');
      const ctrl = new AbortController(); this._sseAbort = ctrl;
      const r = await fetch(url.toString(), { signal: ctrl.signal });
      if (!r.ok || !r.body) throw new Error('debug SSE not available');
      const reader = r.body.getReader(); const dec = new TextDecoder(); let buf='';
      while(true){
        const {value, done} = await reader.read();
        if (done) break;
        buf += dec.decode(value, {stream:true});
        let idx;
        while((idx=buf.indexOf('\n'))>=0){
          const line = buf.slice(0,idx); buf = buf.slice(idx+1);
          if(!line.trim()) continue;
          try{
            const ev = JSON.parse(line);
            const ch = String(ev?.chunk_type||'');
            if (ch==='terminal' || (ch==='status' && ['completed','failed','canceled'].includes(String(ev?.phase||'').toLowerCase()))){
              this.stopDebugStream();
              try{ window.dispatchEvent(new CustomEvent('workers:runsRefresh', {detail:{ worker: this.core.worker }})); }catch{}
              return;
            }
            if (ev) this.events.handleEvent(ev);
          }catch{}
        }
      }
    }catch{
      // If debug SSE not available, just stop (no fallback to poll in debug mode)
      this.stopDebugStream();
    }
  }
  stopDebugStream(){
    if (this._sseAbort){ try{ this._sseAbort.abort(); }catch{} this._sseAbort=null; }
    // keep mode as is until user switches back to observe
  }

  // ===== Replay mode =====
  async startReplay(runId){
    // Stop other modes
    this.stopObserve();
    this.stopDebugStream();
    if (!this._replay) this._replay = new ReplayController(this.core.worker, (ev)=>this.events.handleEvent(ev), api);
    await this._replay.setRun(runId||'');
    // reset view to global overview when selecting a new run
    try{ await this.core.render('overview'); }catch{}
    this.mode='replay'; this.setActive();
  }
  stopReplay(){ if (this._replay){ try{ this._replay.stop(); }catch{} this._replay=null; } }
  replayPrev(){ this._replay && this._replay.prev(); }
  replayNext(){ this._replay && this._replay.next(); }
  replayPlay(intervalMs){ this._replay && this._replay.play((Number.isFinite(intervalMs)? intervalMs : 600)); }
  replayPause(){ this._replay && this._replay.pause(); }
  replayState(){ return this._replay ? this._replay.getState() : {idx:-1,total:0,playing:false,runId:''}; }
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
