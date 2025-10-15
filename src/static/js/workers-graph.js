/**
 * Workers Graph - Latency + Activity Visualization
 * Graph temps réel latence + VAD activity
 */

const MAX_LATENCY_POINTS = 200;
const WINDOW_SPAN_MS = 60000; // 1min

function drawLatencyGraph() {
    const canvas = document.getElementById('latencyCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const w = canvas.parentElement.clientWidth - 48;
    const h = 200;
    
    canvas.width = w;
    canvas.height = h;
    
    ctx.clearRect(0, 0, w, h);
    
    if (!sessionStartTs || latencyPoints.length === 0) {
        ctx.fillStyle = '#9ca3af';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('En attente de données...', w/2, h/2);
        return;
    }
    
    const nowOff = performance.now() - sessionStartTs;
    const tEnd = nowOff;
    const tStart = Math.max(0, tEnd - WINDOW_SPAN_MS);
    
    const pad = {t: 20, r: 20, b: 30, l: 50};
    const chartW = w - pad.l - pad.r;
    const chartH = h - pad.t - pad.b;
    
    // Max latency
    let maxLat = 200;
    latencyPoints.forEach(p => {
        if (p.tStart >= tStart && p.tStart <= tEnd && p.latency > maxLat) {
            maxLat = p.latency;
        }
    });
    maxLat = Math.max(200, Math.ceil(maxLat / 50) * 50);
    
    // Grid
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad.t + (chartH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(w - pad.r, y);
        ctx.stroke();
    }
    
    // Y labels
    ctx.fillStyle = '#6b7280';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
        const val = maxLat - (maxLat / 4) * i;
        const y = pad.t + (chartH / 4) * i;
        ctx.fillText(Math.round(val) + 'ms', pad.l - 8, y + 4);
    }
    
    // Plot latency
    ctx.strokeStyle = '#2563eb';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    let first = true;
    latencyPoints.forEach(p => {
        if (p.tStart < tStart || p.tStart > tEnd) return;
        
        const x = pad.l + ((p.tStart - tStart) / (tEnd - tStart)) * chartW;
        const y = pad.t + chartH - (p.latency / maxLat) * chartH;
        
        if (first) {
            ctx.moveTo(x, y);
            first = false;
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
}
