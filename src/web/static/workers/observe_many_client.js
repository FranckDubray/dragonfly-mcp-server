



















// Observe-many NDJSON client (reconnect loop) with adaptive rate helpers
export function startObserveMany(apply){
  let abort=false;
  // Sliding window counts and history per worker
  const rate = new Map(); // worker -> {ts:number, count:number}
  const history = new Map(); // worker -> number[] (timestamps ms)
  const firstSeen = new Map(); // worker -> first seen ts
  const lastStepAt = new Map(); // worker -> last last_step_at seen (ISO)
  const decayMs = 3000;   // fast window for motion
  const MAX_PER_MIN = 600; // gauge cap for transforms (steps/min)

  function _now(){ return Date.now(); }

  function noteStep(worker){
    const now = _now();
    const r = rate.get(worker) || {ts: now, count: 0};
    if (now - r.ts > decayMs){ r.ts = now; r.count = 0; }
    r.count += 1; r.ts = now; rate.set(worker, r);
    // history list for adaptive windows
    const arr = history.get(worker) || [];
    arr.push(now);
    // prune older than 10 minutes
    const tenMinAgo = now - 10*60*1000;
    while(arr.length && arr[0] < tenMinAgo) arr.shift();
    history.set(worker, arr);
    if (!firstSeen.has(worker)) firstSeen.set(worker, now);
  }

  function getRate(worker){
    const r = rate.get(worker); if (!r) return 0;
    const age = _now() - r.ts; if (age > decayMs) return 0;
    return Math.max(0, Math.min(10, r.count / Math.max(0.5, age/1000)));
  }

  function getAdaptiveRate(worker){
    const now = _now();
    const arr = history.get(worker) || [];
    const seen = firstSeen.get(worker) || now;
    const uptime = now - seen;
    const windowSec = (uptime < 60_000) ? 1 : (uptime < 5*60_000 ? 10 : 60);
    const from = now - windowSec*1000;
    let n = 0; // steps in window
    if (arr.length){
      for (let i=arr.length-1;i>=0;i--){ if (arr[i] >= from) n++; else break; }
    }
    const perSec = n / windowSec;
    const perMin = perSec * 60;
    const ratio = Math.max(0, Math.min(1, perMin / MAX_PER_MIN));
    let unit, value;
    if (windowSec === 1){ unit = 't/s'; value = perSec; }
    else if (windowSec === 10){ unit = 't/10s'; value = perSec * 10; }
    else { unit = 't/min'; value = perMin; }
    return { value, unit, ratio };
  }

  function getToolProgress(startedAtIso, timeoutSec=600){
    if (!startedAtIso) return { ratio: 0, percent: 0 };
    const started = Date.parse(startedAtIso);
    if (!Number.isFinite(started)) return { ratio: 0, percent: 0 };
    const now = _now();
    const elapsed = Math.max(0, (now - started)/1000);
    const ratio = Math.max(0, Math.min(1, elapsed / Math.max(1, timeoutSec)));
    return { ratio, percent: Math.round(ratio*100) };
  }

  async function loop(){
    while(!abort){
      try{
        const url=new URL('/workers/api/observe_many', location.origin);
        url.searchParams.set('timeout_sec','0'); // infinite server-side
        url.searchParams.set('max_events','0'); // unlimited
        const r = await fetch(url.toString()); if(!r.ok) throw new Error('observe_many');
        const reader=r.body.getReader(); const dec=new TextDecoder(); let buf='';
        while(!abort){
          const {value, done}=await reader.read();
          if(done) break;
          buf+=dec.decode(value,{stream:true});
          let idx;
          while((idx=buf.indexOf('\n'))>=0){
            const line=buf.slice(0,idx); buf=buf.slice(idx+1);
            if(!line.trim()) continue;
            try{ 
              const ev=JSON.parse(line);
              const wn = ev?.worker_name || '';
              if (!wn) continue;
              // Only count a step when last_step_at actually changes
              const lastAt = String(ev?.last_step_at || '').trim();
              const prevAt = lastStepAt.get(wn) || '';
              if (lastAt && lastAt !== prevAt){
                noteStep(wn);
                lastStepAt.set(wn, lastAt);
              }
              // callback with helpers
              apply && apply(ev, { getRate, getAdaptiveRate, getToolProgress });
            }catch{}
          }
        }
      }catch{}
      await new Promise(r=>setTimeout(r, 600));
    }
  }
  loop();
  return ()=>{ abort=true; };
}

 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
