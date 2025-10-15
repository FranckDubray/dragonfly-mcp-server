/**
 * Workers Calls - démarrage/fin d'appel inline
 */

function unlockIfNeeded(){
  try { if (typeof unlockAudio === 'function') unlockAudio(); } catch(_){}}

async function callWorker(workerId) {
  if (window.currentCallWorkerId) { alert('Un appel est déjà en cours'); return; }
  unlockIfNeeded();
  try { if (window.ringbackTone) ringbackTone.start(); } catch(_){}
  (window.workersData||[]).forEach(w => {
    const card = document.getElementById(`card-${w.id}`);
    const onlineDot = document.getElementById(`online-${w.id}`);
    const latencyDot = document.getElementById(`latency-${w.id}`);
    const cta = document.getElementById(`cta-${w.id}`);
    if (!card) return;
    if (w.id === workerId) {
      card.classList.add('online');
      if (onlineDot) onlineDot.style.display = 'block';
      if (latencyDot) latencyDot.style.display = 'block';
      if (cta) cta.innerHTML = `<button class="btn btn-ghost" onclick="hangup()">✖️ Raccrocher</button>`;
    } else {
      card.classList.add('disabled');
    }
  });
  const vol = document.getElementById('volumeSlider'); if (vol) vol.style.display = 'block';
  window.currentCallWorkerId = workerId;
  try { await startRealtimeSession({ worker_id: workerId }); }
  catch (error) { alert(`Erreur : ${error.message}`); endCall(); }
}

function endCall() {
  (window.workersData||[]).forEach(w => {
    const card = document.getElementById(`card-${w.id}`);
    const onlineDot = document.getElementById(`online-${w.id}`);
    const latencyDot = document.getElementById(`latency-${w.id}`);
    const cta = document.getElementById(`cta-${w.id}`);
    if (card) card.classList.remove('online', 'disabled');
    if (onlineDot) onlineDot.style.display = 'none';
    if (latencyDot) latencyDot.style.display = 'none';
    if (cta) cta.innerHTML = `<button class="btn btn-primary" onclick="callWorker('${w.id}')">📞 Appeler</button>` + (w.email? ` <a class="btn btn-ghost" href="mailto:${encodeURI(w.email)}" title="Contacter par email">✉️ Email</a>`: '');
  });
  const vol = document.getElementById('volumeSlider'); if (vol) vol.style.display = 'none';
  window.currentCallWorkerId = null;
}

function hangup(){ try { if (typeof closeSession === 'function') closeSession(); } catch(_){} endCall(); }

// Expose
window.callWorker = callWorker;
window.endCall = endCall;
window.hangup = hangup;
window.unlockIfNeeded = unlockIfNeeded;
