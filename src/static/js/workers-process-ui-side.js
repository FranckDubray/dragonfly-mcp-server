
// Workers Process - UI Side panel helpers only
(function(){
  function escapeHtml(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  window.escapeHtml = window.escapeHtml || escapeHtml;
})();
