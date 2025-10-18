
// Workers Process UI Core - small shared helpers
(function(){
  if (typeof WP === 'object' && WP) {
    if (typeof WP.userLockExpires === 'undefined') WP.userLockExpires = 0;
    if (typeof WP.prevReplayLen === 'undefined') WP.prevReplayLen = 0;
    if (typeof WP._initDone === 'undefined') WP._initDone = false;
  }
  function isUserLocked(){ try { return (Date.now() < (WP.userLockExpires||0)); } catch(_) { return false; } }
  function armUserLock(ms){ try { WP.userLockExpires = Date.now() + Math.max(0, ms||5000); } catch(_){} }
  window.WPCoreUtils = { isUserLocked, armUserLock };
})();
