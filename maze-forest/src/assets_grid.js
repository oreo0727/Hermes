(function(global){
  function _loadImage(src){
    return new Promise((resolve,reject)=>{ const img=new Image(); img.onload=()=>resolve(img); img.onerror=reject; img.src=src; });
  }
  function _ensureAtlas(){
    if(!global.Atlas){ global.Atlas = { image:null, frames:new Map(), anim:new Map(), ready:false, scale:1 }; }
    return global.Atlas;
  }
  function _setFrame(Atlas, name, x, y, w, h){
    Atlas.frames.set(name, {x,y,w,h});
  }
  function _addAnim(Atlas, name, frames){
    Atlas.anim.set(name, frames.map(f=>({x:f.x,y:f.y,w:f.w,h:f.h})));
    // Also expose first frame under base key for convenience
    if(frames[0]){ Atlas.frames.set(name, {x:frames[0].x,y:frames[0].y,w:frames[0].w,h:frames[0].h}); }
  }
  function _cellToRect(cellSize, r, c, spanR=1, spanC=1){
    // r,c are 1-indexed
    const x = (c-1)*cellSize;
    const y = (r-1)*cellSize;
    const w = cellSize*spanC;
    const h = cellSize*spanR;
    return {x,y,w,h};
  }

  function _gridSpecSummary(spec){
    const rows = Number(spec.rows || 0);
    const cols = Number(spec.cols || 0);
    const cell = Number(spec.cell || 0);
    const wantW = rows > 0 && cols > 0 && cell > 0 ? cols * cell : 0;
    const wantH = rows > 0 && cols > 0 && cell > 0 ? rows * cell : 0;
    return { rows, cols, cell, wantW, wantH };
  }

  function validateGridAtlasCandidate(img, spec){
    const meta = _gridSpecSummary(spec || {});
    const problems = [];
    if(!img || !img.width || !img.height){
      problems.push("image could not be loaded");
    }
    if(meta.rows > 0 && meta.cols > 0 && meta.cell > 0){
      if(img.width !== meta.wantW || img.height !== meta.wantH){
        problems.push(`expected ${meta.wantW}x${meta.wantH} px for a ${meta.cols}x${meta.rows} grid @ ${meta.cell}px, got ${img.width}x${img.height}`);
      }
    } else if(meta.cell > 0){
      if(img.width % meta.cell !== 0 || img.height % meta.cell !== 0){
        problems.push(`image dimensions are not clean multiples of the ${meta.cell}px cell size`);
      }
    }
    const ok = problems.length === 0;
    return {
      ok,
      problems,
      classification: ok ? "uniform-grid-sheet" : "reference-board-or-wrong-grid",
      message: ok
        ? `Grid atlas candidate matches ${meta.cols || "?"}x${meta.rows || "?"} cells @ ${meta.cell || "?"} px.`
        : (
            "Grid atlas candidate rejected: " +
            problems.join("; ") +
            ". This usually means the file is a labeled reference board, screenshot, or differently packed sheet rather than a build-ready runtime grid atlas."
          ),
    };
  }

  async function installGridAtlas(imageUrl, spec){
    const Atlas = _ensureAtlas();
    const img = await _loadImage(imageUrl + (imageUrl.includes('?')? '&':'?') + 'v=' + (Date.now()%1e8).toString(36));
    const validation = validateGridAtlasCandidate(img, spec);
    if(!validation.ok){
      console.warn(validation.message);
      throw new Error(validation.message);
    }
    Atlas.image = img;
    Atlas.frames = Atlas.frames || new Map();
    Atlas.anim = Atlas.anim || new Map();

    // Fill frames based on mapping spec
    const cell = spec.cell||128;
    const map = spec.map||{};

    function set(name, r,c, spanR,spanC){ const rc=_cellToRect(cell,r,c, spanR||1, spanC||1); _setFrame(Atlas,name, rc.x,rc.y,rc.w,rc.h); }

    // Required by current renderer.js keys
    if(map["terrain/wall-top-n"]) set("terrain/wall-top-n", ...map["terrain/wall-top-n"]);
    if(map["terrain/floor-dirt-var1"]) set("terrain/floor-dirt-var1", ...map["terrain/floor-dirt-var1"]);
    if(map["terrain/floor-dirt-var2"]) set("terrain/floor-dirt-var2", ...map["terrain/floor-dirt-var2"]);
    if(map["terrain/floor-dirt-var3"]) set("terrain/floor-dirt-var3", ...map["terrain/floor-dirt-var3"]);
    if(map["terrain/floor-dirt-var4"]) set("terrain/floor-dirt-var4", ...map["terrain/floor-dirt-var4"]);
    if(map["terrain/door-exit-open"]) set("terrain/door-exit-open", ...map["terrain/door-exit-open"]);
    if(map["hazards/spikes-plate-1"]) set("hazards/spikes-plate-1", ...map["hazards/spikes-plate-1"]);
    if(map["pickups/potion-red-1"]) set("pickups/potion-red-1", ...map["pickups/potion-red-1"]);
    if(map["pickups/shield-blue-1"]) set("pickups/shield-blue-1", ...map["pickups/shield-blue-1"]);
    if(map["pickups/tile-lightning-1"]) set("pickups/tile-lightning-1", ...map["pickups/tile-lightning-1"]);
    if(map["player/hero-walk-1"]) {
      // Allow anim mapping as array of [r,c]
      const seq = Array.isArray(map["player/hero-walk-1"][0]) ? map["player/hero-walk-1"] : [ map["player/hero-walk-1"] ];
      const frames = seq.map(([r,c])=>_cellToRect(cell,r,c));
      _addAnim(Atlas, "player/hero-walk-1", frames);
    }
    if(map["enemies/skeleton-walk-1"]) {
      const seq = Array.isArray(map["enemies/skeleton-walk-1"][0]) ? map["enemies/skeleton-walk-1"] : [ map["enemies/skeleton-walk-1"] ];
      const frames = seq.map(([r,c])=>_cellToRect(cell,r,c));
      _addAnim(Atlas, "enemies/skeleton-walk-1", frames);
    }

    Atlas.ready = true;
    global.SPRITES_READY = true;
    console.log("Grid atlas installed:", imageUrl, "cell", cell);
    return Atlas;
  }

  // Convenience: try to auto-install using our default mapping if user pack is present
  async function tryInstallDefaultUserPack(){
    const url = 'assets/sheets/user-pack.png';
    try{
      const img = await _loadImage(url + '?probe=1');
      if(!img || !img.width || !img.height) return false;
      // Use vision-derived defaults: 768x768, 6x6 grid of 128px cells
      const cell = 128;
      const rows = 6;
      const cols = 6;
      // Vision-derived mapping for the provided user pack (6x6 @ 128px)
      const M = {
        // walls/floors
        "terrain/wall-top-n": [2,2],
        "terrain/floor-dirt-var1": [1,5],
        "terrain/floor-dirt-var2": [1,6],
        "terrain/floor-dirt-var3": [5,5],
        "terrain/floor-dirt-var4": [2,5],
        // door/exit: large ivy stone doorway spanning 2x2 cells at r1-2 c3-4
        "terrain/door-exit-open": [1,3,2,2],
        // hazards and pickups
        "hazards/spikes-plate-1": [4,2],
        "pickups/potion-red-1": [4,4],
        "pickups/shield-blue-1": [4,6],
        "pickups/tile-lightning-1": [5,1],
        // animation sequences
        "player/hero-walk-1": [[3,1],[3,2],[3,3]],
        "enemies/skeleton-walk-1": [[3,4],[3,5]]
      };
      const validation = validateGridAtlasCandidate(img, {cell, rows, cols});
      if(!validation.ok){
        console.warn(validation.message);
        return false;
      }
      await installGridAtlas(url, {cell, rows, cols, map:M});
      return true;
    }catch(_){ return false; }
  }

  global.installGridAtlas = installGridAtlas;
  global.tryInstallDefaultUserPack = tryInstallDefaultUserPack;
  global.validateGridAtlasCandidate = validateGridAtlasCandidate;
})(window);
