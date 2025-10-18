// Workers Process - Render PanZoom (svg-pan-zoom loader + init) <7KB
(function(){
  function loadSvgPanZoom(){
    return new Promise((resolve)=>{
      try{
        if (window.svgPanZoom) return resolve();
        const existing = document.querySelector('script[data-svg-pan-zoom]');
        if (existing){
          const check = ()=>{ if (window.svgPanZoom) resolve(); else setTimeout(check, 50); };
          return check();
        }
        const s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js';
        s.async = true; s.defer = true; s.setAttribute('data-svg-pan-zoom','1');
        s.onload = ()=>{ console.info('[PZ] loader: svg-pan-zoom loaded'); resolve(); };
        s.onerror = ()=>{
          console.warn('[PZ] loader: CDN failed, fallback to local');
          try{
            const l = document.createElement('script');
            l.src = '/static/vendor/svg-pan-zoom.min.js';
            l.async = true; l.defer = true; l.setAttribute('data-svg-pan-zoom','1');
            l.onload = ()=>{ console.info('[PZ] loader: fallback local loaded'); resolve(); };
            l.onerror = ()=>{ console.warn('[PZ] loader: local fallback failed'); resolve(); };
            document.head.appendChild(l);
          }catch(_){ resolve(); }
        };
        document.head.appendChild(s);
      }catch(_){ resolve(); }
    });
  }

  function parseViewBox(svg){
    try{ const vb = String(svg.getAttribute('viewBox')||'').trim().split(/\s+/).map(parseFloat); if (vb.length===4 && isFinite(vb[2]) && isFinite(vb[3])) return {x:vb[0], y:vb[1], w:vb[2], h:vb[3]}; }catch(_){ }
    return {x:0,y:0,w:0,h:0};
  }

  function fitHeightAndAlignLeft(svgEl){
    try{
      if (!svgEl || !svgEl.__df_pz) return;
      if (svgEl.__df_fitting) return; svgEl.__df_fitting = true;

      let vpH = 0, vbH = 0, vpW = 0, vbW = 0;
      try{ const s = svgEl.__df_pz.getSizes(); vpH = Number(s?.viewport?.height)||0; vpW = Number(s?.viewport?.width)||0; vbH = Number(s?.viewBox?.height)||0; vbW = Number(s?.viewBox?.width)||0; }catch(_){ }
      if (vpH<=0 || vpW<=0){ const r = svgEl.getBoundingClientRect(); vpH = vpH || (r.height||0); vpW = vpW || (r.width||0); }
      if (vbH<=0 || vbW<=0){ const vb = parseViewBox(svgEl); vbH = vbH || (vb.h||0); vbW = vbW || (vb.w||0); }
      if (vpH>0 && vbH>0){
        const desiredH = vpH / vbH; // zoom absolu pour coller la HAUTEUR
        const minWidthRatio = 0.6;  // au moins 60% de la largeur visible
        const desiredW = vbW>0 ? (minWidthRatio * vpW) / vbW : desiredH;
        const target = Math.max(desiredH, desiredW);

        // Stabilisation: si paramètres + zoom déjà appliqués (≈), ne rien faire
        const last = svgEl.__df_last || {};
        if (last.vpW===vpW && last.vpH===vpH && last.vbW===vbW && last.vbH===vbH && Math.abs((last.zoom||0)-target) < 0.01){
          console.info('[PZ] heightZoom skip (stable)');
        } else {
          const curr = (typeof svgEl.__df_pz.getZoom === 'function') ? (svgEl.__df_pz.getZoom()||1) : 1;
          const delta = target / curr;
          const point = { x: 0, y: vpH/2 };
          try { svgEl.__df_pz.zoomAtPointBy(delta, point); } catch(_){ try{ svgEl.__df_pz.zoom(target); }catch(_){ } }
          console.info('[PZ] zoomFloor', { desiredH, desiredW, target, vpH, vbH, vpW, vbW });

          // Alignement horizontal: enlever la marge gauche (le SVG est centré par défaut avec meet)
          try{
            const z = svgEl.__df_pz.getZoom?.() || target;
            const scaledW = (vbW||0) * z;
            const leftover = Math.max(0, vpW - scaledW);
            console.info('[PZ] width calc', { vpW, vbW, z, scaledW, leftover });
            if (leftover > 1){
              const cur = svgEl.__df_pz.getPan?.() || {x:0,y:0};
              svgEl.__df_pz.pan({ x: cur.x + leftover/2, y: cur.y });
            }
          }catch(_){ }
        }
        svgEl.__df_last = { vpW, vpH, vbW, vbH, zoom: target };
      } else {
        console.warn('[PZ] heightZoom skipped (vp/vb invalid)', {vpH, vbH, vpW, vbW});
      }
    }catch(e){ console.warn('[PZ] heightZoom error', e); }
    finally { try{ svgEl.__df_fitting = false; }catch(_){ } }
  }

  function ensurePanZoom(svgEl){
    try{
      if (!window.svgPanZoom || !svgEl) return;
      try{ svgEl.__df_pz && svgEl.__df_pz.destroy && svgEl.__df_pz.destroy(); }catch(_){ }
      const pz = window.svgPanZoom(svgEl, {
        panEnabled: true,
        zoomEnabled: true,
        mouseWheelZoomEnabled: true,
        dblClickZoomEnabled: true,
        preventMouseEventsDefault: true,
        controlIconsEnabled: false,
        fit: true,
        center: false,
        minZoom: 0.05,
        maxZoom: 50
      });
      svgEl.__df_pz = pz;

      // Initial pass: fit + custom heightZoom
      try{ pz.resize(); pz.fit(); fitHeightAndAlignLeft(svgEl); }catch(_){ }
      // Passes tardives (sans pz.fit() pour éviter recentrage)
      try{ requestAnimationFrame(()=>{ try{ pz.resize(); fitHeightAndAlignLeft(svgEl); }catch(_){ } }); }catch(_){ }
      setTimeout(()=>{ try{ pz.resize(); fitHeightAndAlignLeft(svgEl); }catch(_){ } }, 140);

      // RO container & window resize (debounced by __df_fitting guard)
      try{
        const container = document.getElementById('processGraph');
        if (container){
          if (container.__df_pz_ro){ try{ container.__df_pz_ro.disconnect(); }catch(_){ } }
          const ro = new ResizeObserver(()=>{ try{ pz.resize(); fitHeightAndAlignLeft(svgEl); }catch(_){ } });
          ro.observe(container);
          container.__df_pz_ro = ro;
        }
      }catch(_){ }

      if (!window.__df_pz_resize){
        window.__df_pz_resize = () => {
          try{ const cur = document.querySelector('#processGraph .mermaid-graph svg'); if (cur && cur.__df_pz){ cur.__df_pz.resize(); fitHeightAndAlignLeft(cur); } }catch(_){ }
        };
        window.addEventListener('resize', window.__df_pz_resize);
      }
      console.info('[PZ] init ok, heightZoom applied');
    }catch(e){ console.warn('[PZ] init failed', e); }
  }

  window.RenderPanZoom = { loadSvgPanZoom, ensurePanZoom, fitHeightAndAlignLeft };
})();
