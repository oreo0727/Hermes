/*
 Maze Forest — Runtime Stability Shim v1
 Purpose: stop "all over the place" sprites by fixing DPR scaling, disabling smoothing,
 and guarding drawImage() calls so bad UVs don't sample random atlas regions.

 Safe to include early in index.html. No build step required. Reversible.
*/
(function(){
  const d = window.document;
  const log = (...args)=>console.log('[MazeShim]', ...args);

  function installCanvasCrisp(canvas){
    if(!canvas) return;
    const ctx = canvas.getContext('2d');
    if(!ctx) return;
    function fit(){
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      // Use client dimensions (CSS pixels)
      const cssW = Math.floor(canvas.clientWidth || canvas.width || 0);
      const cssH = Math.floor(canvas.clientHeight || canvas.height || 0);
      if(!cssW || !cssH) return; // hidden or not laid out yet
      const needResize = (canvas.width !== cssW * dpr) || (canvas.height !== cssH * dpr);
      if(needResize){
        canvas.width = cssW * dpr;
        canvas.height = cssH * dpr;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.imageSmoothingEnabled = false;
      // Some browsers honour these CSS hints for image elements drawn later
      canvas.style.imageRendering = 'pixelated';
    }
    window.addEventListener('resize', fit, {passive:true});
    // Fit now and once more after layout stabilizes
    fit();
    setTimeout(fit, 0);
    log('Canvas crisp installed (DPR-fit + smoothing off)');
  }

  // Guard drawImage to avoid fractional/out-of-bounds sampling on atlases.
  // If a 9-arg call looks invalid or fractional, we round and clamp.
  // If still invalid, draw a readable fallback tile instead of garbage fragments.
  function installDrawImageGuard(){
    const proto = window.CanvasRenderingContext2D && window.CanvasRenderingContext2D.prototype;
    if(!proto) return;
    if(proto.__mazeGuardInstalled) return;
    const _drawImage = proto.drawImage;
    proto.drawImage = function(img, sx, sy, sw, sh, dx, dy, dw, dh){
      try{
        if(arguments.length === 9){
          // Validate image natural size
          const iw = (img && (img.naturalWidth || img.videoWidth || img.width)) || 0;
          const ih = (img && (img.naturalHeight || img.videoHeight || img.height)) || 0;
          // Coerce to numbers
          sx = +sx; sy = +sy; sw = +sw; sh = +sh; dx = +dx; dy = +dy; dw = +dw; dh = +dh;
          // Round source rect to integers to avoid sampling across cell edges
          sx = Math.round(sx); sy = Math.round(sy); sw = Math.round(sw); sh = Math.round(sh);
          // Clamp within image bounds
          if (sw < 1 || sh < 1 || iw < 1 || ih < 1 || !isFinite(sx) || !isFinite(sy)){
            // Fallback: draw a readable block instead of garbage
            this.save();
            this.fillStyle = '#885';
            this.fillRect(Math.round(dx), Math.round(dy), Math.round(dw), Math.round(dh));
            this.restore();
            return;
          }
          if (sx < 0) { sw += sx; sx = 0; }
          if (sy < 0) { sh += sy; sy = 0; }
          if (sx + sw > iw) { sw = iw - sx; }
          if (sy + sh > ih) { sh = ih - sy; }
          // Nudge inwards to reduce atlas edge bleed when no extrusion/padding
          if (sw > 2 && sh > 2){ sx += 1; sy += 1; sw -= 2; sh -= 2; }
          // Dest rounding for crisp edges
          dx = Math.round(dx); dy = Math.round(dy); dw = Math.round(dw); dh = Math.round(dh);
          return _drawImage.call(this, img, sx, sy, sw, sh, dx, dy, dw, dh);
        }
        // 3-arg form or 5-arg form: let it pass but prefer integer dest coords
        if(arguments.length === 3){
          const dx = Math.round(arguments[1]);
          const dy = Math.round(arguments[2]);
          return _drawImage.call(this, arguments[0], dx, dy);
        }
        if(arguments.length === 5){
          const dx = Math.round(arguments[3]);
          const dy = Math.round(arguments[4]);
          return _drawImage.call(this, arguments[0], arguments[1], arguments[2], dx, dy);
        }
        return _drawImage.apply(this, arguments);
      }catch(e){
        // As an absolute last resort, draw a block to avoid mosaic garbage
        try{
          if(arguments.length === 9){
            const dx = Math.round(arguments[5]); const dy = Math.round(arguments[6]);
            const dw = Math.round(arguments[7]); const dh = Math.round(arguments[8]);
            this.save(); this.fillStyle = '#885'; this.fillRect(dx, dy, dw, dh); this.restore();
            return;
          }
        }catch(_){/* ignore */}
        throw e;
      }
    };
    Object.defineProperty(proto, '__mazeGuardInstalled', {value:true});
    log('drawImage guard installed');
  }

  // Auto-detect the main game canvas (#game) and install crispness.
  function boot(){
    const canvas = d.getElementById('game') || d.querySelector('canvas');
    if(canvas) installCanvasCrisp(canvas);
    installDrawImageGuard();
  }

  if(d.readyState === 'loading') d.addEventListener('DOMContentLoaded', boot, {once:true});
  else boot();

  // Expose for manual installs in game code if needed
  window.installMazeCrisp = installCanvasCrisp;
})();
