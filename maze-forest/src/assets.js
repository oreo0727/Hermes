(function(global){
  const Atlas = {
    image: null,
    frames: new Map(), // name -> {x,y,w,h}
    anim: new Map(),   // baseName -> [{x,y,w,h}, ...]
    ready: false,
    scale: 1,
  };

  function _loadImage(src){
    return new Promise((resolve,reject)=>{ const img=new Image(); img.onload=()=>resolve(img); img.onerror=reject; img.src=src; });
  }

  async function loadAtlas(jsonUrl){
    const v = (Date.now()%1e8).toString(36); // cache-bust by default
    const url = jsonUrl.includes('?') ? jsonUrl : jsonUrl+`?v=${v}`;
    const res = await fetch(url);
    if(!res.ok) throw new Error(`Failed to load atlas JSON: ${res.status}`);
    const data = await res.json();
    // Heuristic: image alongside JSON named spritesheet.png
    const base = jsonUrl.replace(/[^/]+$/, '');
    const imgUrl = base + 'spritesheet.png' + (jsonUrl.includes('?')? '&':'?') + `v=${v}`;
    const img = await _loadImage(imgUrl);

    Atlas.image = img;
    Atlas.frames.clear();
    Atlas.anim.clear();

    // Expect either: {name:{x,y,w,h,origin,frames?}} or separate anim entries like name.anim
    for(const [name, entry] of Object.entries(data)){
      if(entry && Array.isArray(entry.frames) && entry.frames.length){
        Atlas.anim.set(name.replace(/\.anim$/, ''), entry.frames.map(f=>({x:f.x,y:f.y,w:f.w,h:f.h})));
        // Also expose the first frame under the base name for convenience
        const first = entry.frames[0];
        Atlas.frames.set(name.replace(/\.anim$/, ''), {x:first.x,y:first.y,w:first.w,h:first.h});
      } else if(entry && typeof entry.x==='number'){
        Atlas.frames.set(name, {x:entry.x,y:entry.y,w:entry.w,h:entry.h});
        if(entry.frames && Array.isArray(entry.frames)){
          Atlas.anim.set(name, entry.frames.map(f=>({x:f.x,y:f.y,w:f.w,h:f.h})));
        }
      }
    }

    Atlas.ready = true;
    global.SPRITES_READY = true;
    return Atlas;
  }

  function getAnim(name){
    if(Atlas.anim.has(name)) return Atlas.anim.get(name);
    // Try stripping numeric suffixes like -1
    const base = name.replace(/-[0-9]+$/, '');
    if(Atlas.anim.has(base)) return Atlas.anim.get(base);
    return null;
  }

  function getFrame(name, frameIndex=0){
    const seq = getAnim(name);
    if(seq && seq[frameIndex%seq.length]) return seq[frameIndex%seq.length];
    const f = Atlas.frames.get(name) || Atlas.frames.get(name.replace(/-[0-9]+$/,''));
    return f || null;
  }

  function drawSprite(ctx, name, x, y, size, opts={}){
    if(!Atlas.ready || !Atlas.image) return false;
    const frameIndex = (opts.frameIndex||0) >>> 0;
    const f = getFrame(name, frameIndex);
    if(!f) return false;
    const dw = (opts.w || size || f.w);
    const dh = (opts.h || size || f.h);
    const dx = Math.floor(x + (opts.center? 0 : 0));
    const dy = Math.floor(y + (opts.center? 0 : 0));
    ctx.drawImage(Atlas.image, f.x, f.y, f.w, f.h, dx, dy, dw, dh);
    return true;
  }

  global.Atlas = Atlas;
  global.loadAtlas = loadAtlas;
  global.drawSprite = drawSprite;
})(window);
