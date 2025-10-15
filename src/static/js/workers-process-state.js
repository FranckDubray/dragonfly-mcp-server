



// Workers Process - Shared state
(function(){
  window.WP = {
    mermaidReady: false,
    replayTimer: null,
    replayActive: false,
    replayIx: 0,
    replaySeq: [],
    processWorkerId: '',
    processRefreshTimer: null,
    atTail: true, // nouveau: indique si on est positionné sur la dernière étape
  };
})();

 
 
 
 
 