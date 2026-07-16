(function(){
  // Optional helper to choose best-fit spritesheet (1x/2x/3x) when larger assets are available.
  // Usage: const url = window.pickAtlasUrl('/assets/sheets/spritesheet.json');
  function pickAtlasUrl(baseJsonUrl, opts){
    const o = opts||{};
    const dpr = Math.max(1, window.devicePixelRatio||1);
    const ts = (window.MAZE_OPTS && window.MAZE_OPTS.targetTile) || 72;
    // Effective required pixels per tile (rough heuristic):
    const need = ts * dpr;
    // Buckets map
    // Expect files like spritesheet.json (1x), spritesheet@2x.json, spritesheet@3x.json
    const parts = baseJsonUrl.split('.');
    const ext = parts.pop();
    const stem = parts.join('.');
    let bucket = '1x';
    if (need >= 128) bucket = '3x';
    else if (need >= 80) bucket = '2x';
    // Prefer the highest bucket not exceeding need; allow override
    if (o.force) bucket = o.force;
    const url = bucket==='1x' ? `${stem}.${ext}` : `${stem}@${bucket}.${ext}`;
    return url;
  }
  window.pickAtlasUrl = pickAtlasUrl;
})();
