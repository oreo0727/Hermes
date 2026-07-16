(function(){
  const NICE = [96, 88, 80, 72, 64, 56, 48, 40, 32, 24, 16, 12, 8];

  function computeTileSize(W,H,rows,cols,targetPx){
    const maxTs = Math.floor(Math.min(W/cols, H/rows));
    let ts = maxTs;
    const desire = Math.min(maxTs, Math.max(8, targetPx||72));
    // Pick the NICE size closest to the desired, but not exceeding maxTs by more than 10%
    let best = ts, bestDiff = 1e9;
    for (let i=0;i<NICE.length;i++){
      const n = NICE[i];
      if (n <= Math.max(8, maxTs*1.1)){
        const d = Math.abs(n - desire);
        if (d < bestDiff){ bestDiff = d; best = n; }
      }
    }
    ts = Math.min(best, maxTs);
    if (!ts || !isFinite(ts)) ts = Math.max(8, Math.floor(maxTs)||16);
    return ts;
  }

  function scaleEntity(base, scale){
    return base * (scale || 1);
  }

  // Expose to global for renderer usage
  window.computeTileSize = computeTileSize;
  window.scaleEntity = scaleEntity;
})();
