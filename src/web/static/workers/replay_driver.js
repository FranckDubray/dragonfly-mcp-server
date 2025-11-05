




























export class ReplayController{
  constructor(worker, onEvent, api){
    this.worker = worker;
    this.onEvent = onEvent;
    this.api = api;
    this.steps = [];
    this.idx = -1;
    this._timer = 0;
    this._playing = false;
    this._runId = '';
  }
  async setRun(runId){
    this.stop();
    this._runId = runId || '';
    if (!runId) { this.steps=[]; return; }
    try{
      const steps = await this.api.replaySteps(this.worker, runId, 1000);
      this.steps = Array.isArray(steps)? steps : [];
    }catch{ this.steps = []; }
    this.idx = -1;
  }
  _emitFromStep(st){
    if (!st) return;
    const ev = {
      chunk_type: 'replay',
      node_executed: st.node || '',
      status: st.status || '',
      started_at: st.started_at || '',
      finished_at: st.finished_at || '',
      io: { in: (st.io && st.io.in) || {}, out_preview: (st.io && st.io.out_preview) || '' }
    };
    try{ this.onEvent && this.onEvent(ev); }catch{}
  }
  next(){
    if (!this.steps.length) return;
    this.idx = Math.min(this.idx + 1, this.steps.length - 1);
    this._emitFromStep(this.steps[this.idx]);
  }
  prev(){
    if (!this.steps.length) return;
    this.idx = Math.max(this.idx - 1, 0);
    this._emitFromStep(this.steps[this.idx]);
  }
  jumpTo(index){
    if (!this.steps.length) return;
    const i = Math.max(0, Math.min(index|0, this.steps.length-1));
    this.idx = i;
    this._emitFromStep(this.steps[this.idx]);
  }
  play(intervalMs=600){
    if (this._playing || !this.steps.length) return;
    this._playing = true;
    const MIN_INTERVAL = 80; // avoid 0ms tight loop which can flood rendering
    const loop = () => {
      if (!this._playing) return;
      if (this.idx >= this.steps.length - 1){ this.stop(); return; }
      this.next();
      const sleep = Math.max(MIN_INTERVAL, Number.isFinite(intervalMs) ? intervalMs : 600);
      this._timer = setTimeout(loop, sleep);
    };
    loop();
  }
  pause(){ this._playing=false; if (this._timer) clearTimeout(this._timer); this._timer=0; }
  stop(){ this.pause(); this.idx=-1; }
  getState(){ return { runId:this._runId, idx:this.idx, total:this.steps.length, playing:this._playing }; }
}

 

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
