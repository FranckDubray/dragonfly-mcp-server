/**
 * Workers VAD - Voice Activity Detection
 * SIMPLIFIÉ : Server VAD géré par OpenAI Realtime
 * Ce fichier est conservé pour compatibilité future (graph activity)
 */

let audioCtx = null;
let userAnalyser = null;
let aiAnalyser = null;
let userBuf = null;
let aiBuf = null;
let vadTimer = null;

let userSpeaking = false;
let aiSpeaking = false;
let lastUserSpeaking = false;

// Activity tracking pour graph
let userActivity = [];
let aiActivity = [];
let sessionStartTs = null;

async function initAudioContext() {
    if (audioCtx) return audioCtx;
    
    const Ctx = window.AudioContext || window.webkitAudioContext;
    audioCtx = new Ctx();
    
    try {
        await audioCtx.resume();
    } catch (e) {
        console.warn('Failed to resume AudioContext:', e);
    }
    
    return audioCtx;
}

function setupLocalAnalyser(stream) {
    if (!audioCtx) return;
    
    try {
        const source = audioCtx.createMediaStreamSource(stream);
        userAnalyser = audioCtx.createAnalyser();
        userAnalyser.fftSize = 2048;
        userAnalyser.smoothingTimeConstant = 0.2;
        source.connect(userAnalyser);
        userBuf = new Uint8Array(userAnalyser.fftSize);
        
        console.log('✅ User analyser setup (optionnel, server_vad actif)');
    } catch (e) {
        console.error('Failed to setup user analyser:', e);
    }
}

function setupRemoteAnalyser(stream) {
    if (!audioCtx) return;
    
    try {
        const source = audioCtx.createMediaStreamSource(stream);
        aiAnalyser = audioCtx.createAnalyser();
        aiAnalyser.fftSize = 2048;
        aiAnalyser.smoothingTimeConstant = 0.2;
        source.connect(aiAnalyser);
        aiBuf = new Uint8Array(aiAnalyser.fftSize);
        
        console.log('✅ AI analyser setup (optionnel, server_vad actif)');
    } catch (e) {
        console.error('Failed to setup AI analyser:', e);
    }
}

function startVADLoop() {
    // NOTE : Server VAD gère déjà turn_detection
    // Cette boucle est OPTIONNELLE (pour visualisation graph uniquement)
    stopVADLoop();
    
    sessionStartTs = performance.now();
    userActivity = [{t: 0, speaking: false}];
    aiActivity = [{t: 0, speaking: false}];
    
    vadTimer = setInterval(sampleVAD, 120); // 120ms sampling
    console.log('✅ VAD loop started (graph only, server_vad actif)');
}

function stopVADLoop() {
    if (vadTimer) {
        clearInterval(vadTimer);
        vadTimer = null;
    }
    userAnalyser = null;
    aiAnalyser = null;
}

function sampleVAD() {
    let changed = false;
    
    // User speaking detection (optionnel, graph only)
    if (userAnalyser && userBuf) {
        userAnalyser.getByteTimeDomainData(userBuf);
        const rmsUser = computeRMSByte(userBuf);
        
        // Hysteresis thresholds
        const newUserSpeaking = userSpeaking ? (rmsUser > 0.018) : (rmsUser > 0.035);
        
        if (newUserSpeaking !== userSpeaking) {
            userSpeaking = newUserSpeaking;
            pushActivity(userActivity, userSpeaking);
            changed = true;
        }
    }
    
    // AI speaking detection (optionnel, graph only)
    if (aiAnalyser && aiBuf) {
        aiAnalyser.getByteTimeDomainData(aiBuf);
        const rmsAI = computeRMSByte(aiBuf);
        
        const newAiSpeaking = aiSpeaking ? (rmsAI > 0.015) : (rmsAI > 0.030);
        
        if (newAiSpeaking !== aiSpeaking) {
            aiSpeaking = newAiSpeaking;
            pushActivity(aiActivity, aiSpeaking);
            changed = true;
        }
    }
    
    // NOTE : Pas besoin d'envoyer cancel ici, server_vad gère l'interruption
    
    lastUserSpeaking = userSpeaking;
    
    if (changed) {
        console.log('[VAD] Activity (graph only):', {user: userSpeaking, ai: aiSpeaking});
    }
    
    // Redraw graph
    if (typeof drawLatencyGraph === 'function') {
        drawLatencyGraph();
    }
}

function computeRMSByte(arr) {
    let sum = 0;
    const n = arr.length;
    
    for (let i = 0; i < n; i++) {
        const v = (arr[i] - 128) / 128;
        sum += v * v;
    }
    
    return Math.sqrt(sum / n);
}

function pushActivity(timeline, speaking) {
    if (!sessionStartTs) return;
    
    const t = performance.now() - sessionStartTs;
    const last = timeline[timeline.length - 1];
    
    if (!last || last.speaking !== speaking) {
        timeline.push({t, speaking});
    }
}
