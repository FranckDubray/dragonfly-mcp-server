// Edge effects: fuse animation between nodes, and pulse on entry
export function animateFuse(svg, fromG, toG, opts={}){
  try{
    const dur = Math.max(200, Math.min(1200, opts.durationMs||500));
    const col = opts.color || '#f97316';
    const bb1 = fromG.getBBox(), bb2 = toG.getBBox();
    const x1 = bb1.x + bb1.width/2, y1 = bb1.y + bb1.height/2;
    const x2 = bb2.x + bb2.width/2, y2 = bb2.y + bb2.height/2;

    const ov = document.createElementNS('http://www.w3.org/2000/svg','g');
    ov.classList.add('edge-fx');
    const path = document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('d', `M ${x1} ${y1} L ${x2} ${y2}`);
    path.setAttribute('stroke', col);
    path.setAttribute('fill', 'none');
    path.style.animationDuration = (dur/1000)+'s';
    ov.appendChild(path);
    const spark = document.createElementNS('http://www.w3.org/2000/svg','circle');
    spark.setAttribute('r','3'); spark.classList.add('spark');
    ov.appendChild(spark);
    svg.appendChild(ov);

    const start = performance.now();
    function step(t){
      const p = Math.min(1, (t-start)/dur);
      const cx = x1 + (x2-x1)*p, cy = y1 + (y2-y1)*p;
      spark.setAttribute('cx', cx); spark.setAttribute('cy', cy);
      if (p < 1) requestAnimationFrame(step);
      else setTimeout(()=>{ try{ ov.remove(); }catch{} }, 80);
    }
    requestAnimationFrame(step);
    return { cancel: ()=>{ try{ ov.remove(); }catch{} } };
  }catch(e){ return { cancel: ()=>{} }; }
}

export function animatePulse(svg, atG, opts={}){
  try{
    const bb = atG.getBBox();
    const x = bb.x + bb.width/2, y = bb.y + bb.height/2;
    const ov = document.createElementNS('http://www.w3.org/2000/svg','g');
    ov.classList.add('edge-fx');
    const c = document.createElementNS('http://www.w3.org/2000/svg','circle');
    c.setAttribute('cx',x); c.setAttribute('cy',y); c.setAttribute('r','3');
    c.setAttribute('fill','#f97316');
    ov.appendChild(c); svg.appendChild(ov);
    let k=0; const times = Math.max(1,Math.min(3, opts.times||1));
    function pulse(){
      k+=1; c.setAttribute('r','3'); c.style.opacity='1';
      c.animate([{r:3, opacity:1},{r:9, opacity:.0}], {duration:320, fill:'forwards'});
      if (k<times) setTimeout(pulse, 100);
      else setTimeout(()=>{ try{ ov.remove(); }catch{} }, 350);
    }
    pulse();
    return { cancel: ()=>{ try{ ov.remove(); }catch{} } };
  }catch(e){ return { cancel: ()=>{} }; }
}
