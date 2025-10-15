/**
 * Workers UI - inline call controls, avatar ring animation
 */

(function(){
  let currentId = null;
  let speaking = false;

  function setSpeaking(workerId, value){
    speaking = !!value;
    const ring = document.querySelector(`#card-${workerId} .worker-avatar`);
    if (!ring) return;
    ring.classList.toggle('speaking', speaking);
  }

  function setOnline(workerId, on){
    const card = document.getElementById(`card-${workerId}`);
    const dot = document.getElementById(`online-${workerId}`);
    if (card) card.classList.toggle('online', !!on);
    if (dot) dot.style.display = on ? 'block' : 'none';
  }

  // Hooks pour session.js
  window.uiHooks = {
    onCallStart(workerId){
      currentId = workerId;
      setOnline(workerId, true);
      const transcripts = document.getElementById(`transcripts-${workerId}`);
      const cta = document.getElementById(`cta-${workerId}`);
      if (transcripts) transcripts.style.display = 'block';
      if (cta) cta.style.display = 'none';
      const vol = document.getElementById('volumeSlider');
      if (vol) vol.style.display = 'block';
    },
    onCallEnd(){
      if (!currentId) return;
      setOnline(currentId, false);
      const transcripts = document.getElementById(`transcripts-${currentId}`);
      const cta = document.getElementById(`cta-${currentId}`);
      if (transcripts) transcripts.style.display = 'none';
      if (cta) cta.style.display = 'block';
      const vol = document.getElementById('volumeSlider');
      if (vol) vol.style.display = 'none';
      currentId = null;
    },
    onAISpeaking(workerId, value){ setSpeaking(workerId, value); },
  };
})();
