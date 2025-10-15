
/**
 * Workers Grid - Affichage & interactions cartes (inline call)
 * - Rendu cartes (avatar, méta, icônes, stats, événements, CTA)
 * - Démarrage/fin d'appel (inline) -> délégué à workers-calls.js
 * - Rafraîchissement stats + derniers événements (non intrusif)
 * NOTE: Galerie (workers-gallery.js) & Process (workers-process.js) sont découpés.
 */

window.workersData = [];
// Utiliser un état global unique pour éviter les décalages de modules
if (typeof window.currentCallWorkerId === 'undefined') window.currentCallWorkerId = null;

function unlockIfNeeded(){
  try { if (typeof unlockAudio === 'function') unlockAudio(); } catch(_){}
  try {
    if (window.audioPlayer) window.audioPlayer.setVolume(0.5); // défaut 50%
    const volSlider = document.querySelector('#volumeSlider input[type="range"]');
    if (volSlider) volSlider.value = 0.5;
  } catch(_){}
}

async function loadWorkers() {
    const grid = document.getElementById('workersGrid');
    try {
        const response = await fetch('/workers');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        window.workersData = data.workers || [];
        if (window.workersData.length === 0) {
            grid.innerHTML = '<div class="loading-state"><p>Aucun worker trouvé</p></div>';
            return;
        }
        grid.innerHTML = window.workersData.map(worker => renderWorkerCard(worker)).join('');
        for (const worker of window.workersData) {
            await refreshWorkerStats(worker.id);
            await refreshWorkerEvents(worker.id, 3); // 3 derniers événements, sobre
        }
    } catch (error) {
        console.error('Failed to load workers:', error);
        grid.innerHTML = `<div class="loading-state">
            <p style="color: var(--danger);">❌ Erreur de chargement</p>
            <p style="font-size: 12px;">${error.message}</p>
        </div>`;
    }
}

// Déléguer les appels à workers-calls.js pour éviter les doublons
function callWorker(workerId){ if (window && typeof window.callWorker === 'function' && window.callWorker !== callWorker){ return window.callWorker(workerId); } }
function endCall(){ if (window && typeof window.endCall === 'function' && window.endCall !== endCall){ return window.endCall(); } }
function hangup(){ if (window && typeof window.hangup === 'function' && window.hangup !== hangup){ return window.hangup(); } }

// ===== Stats & Événements =====
setInterval(async () => {
  for (const w of window.workersData){
    await refreshWorkerStats(w.id);
    await refreshWorkerEvents(w.id, 3);
  }
}, 30000);

// Expose pour modules externes
window.loadWorkers = loadWorkers;
// Ne pas ré-exposer callWorker/endCall/hangup ici pour éviter l'écrasement
