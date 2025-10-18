
/**
 * Workers Grid - Affichage & interactions cartes (inline call)
 * NOTE: Ne plus définir unlockIfNeeded ici (déplacé dans workers-calls.js)
 */

window.workersData = [];
if (typeof window.currentCallWorkerId === 'undefined') window.currentCallWorkerId = null;

// Supprimé: function unlockIfNeeded() - doit rester unique dans workers-calls.js

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
            await refreshWorkerEvents(worker.id, 3);
        }
    } catch (error) {
        console.error('Failed to load workers:', error);
        grid.innerHTML = `<div class="loading-state">
            <p style="color: var(--danger);">❌ Erreur de chargement</p>
            <p style="font-size: 12px;">${error.message}</p>
        </div>`;
    }
}

function callWorker(workerId){ if (window && typeof window.callWorker === 'function' && window.callWorker !== callWorker){ return window.callWorker(workerId); } }
function endCall(){ if (window && typeof window.endCall === 'function' && window.endCall !== endCall){ return window.endCall(); } }
function hangup(){ if (window && typeof window.hangup === 'function' && window.hangup !== hangup){ return window.hangup(); } }

setInterval(async () => {
  for (const w of window.workersData){
    await refreshWorkerStats(w.id);
    await refreshWorkerEvents(w.id, 3);
  }
}, 30000);

window.loadWorkers = loadWorkers;
