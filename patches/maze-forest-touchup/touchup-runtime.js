(function(){
  function setImageSmoothing(ctx, enabled){
    if (!ctx) return;
    ctx.imageSmoothingEnabled = !!enabled;
    try { ctx.imageSmoothingQuality = enabled ? 'high' : 'low'; } catch(e){}
  }

  function installCanvasCrisp(canvas, ctx){
    if (!canvas || !ctx) return;
    // CSS hints for crisp scaling
    try {
      canvas.style.imageRendering = 'pixelated';
      canvas.style.setProperty('image-rendering','pixelated');
      canvas.style.setProperty('image-rendering','crisp-edges');
    } catch(e){}
    setImageSmoothing(ctx, false);

    // Also intercept getContext to re-disable smoothing if contexts are recreated
    const _getContext = canvas.getContext.bind(canvas);
    canvas.getContext = function(type, opts){
      const c = _getContext(type, opts);
      setImageSmoothing(c, false);
      return c;
    };
  }

  // Snap a logical coordinate to the nearest device-pixel boundary
  function snapPx(v, dpr){
    const r = Math.round((v||0) * (dpr||1)) / (dpr||1);
    return r;
  }

  // Pick a nice crisp tile size from candidates near the target
  function computeNiceTileSize(W, H, rows, cols, target){
    const dpr = Math.max(1, window.devicePixelRatio||1);
    const maxW = Math.floor((W||0));
    const maxH = Math.floor((H||0));
    if (!rows || !cols || !maxW || !maxH) return Math.floor(target||72);
    const fitW = Math.floor(maxW / cols);
    const fitH = Math.floor(maxH / rows);
    const fit = Math.max(16, Math.min(fitW, fitH));
    const wish = Math.min(fit, Math.floor(target||72));
    // prefer sizes divisible by 2/3/4 to minimize shimmer
    const candidates = [96, 88, 80, 76, 72, 68, 64, 60, 56, 48, 40, 32, 24, 16]
      .filter(n => n <= fit && n <= Math.max(wish, 16));
    if (candidates.length) return candidates[0];
    return Math.floor(Math.max(16, Math.min(fit, wish)));
  }

  // Gentler vignette post-pass (call at end of frame if you have no built-in control)
  function touchupEndOfFrame(ctx, w, h, dpr){
    const opts = (window.MAZE_OPTS||{}).vignette||{};
    const strength = Math.max(0, Math.min(1, opts.strength==null ? 0.35 : opts.strength));
    const radius = Math.max(0.1, Math.min(1.5, opts.radius==null ? 0.90 : opts.radius));
    if (!ctx || !w || !h || !strength) return;
    const cx = w/2, cy = h/2;
    const r = Math.hypot(cx, cy) * radius;
    const g = ctx.createRadialGradient(cx, cy, r*0.25, cx, cy, r);
    g.addColorStop(0, `rgba(0,0,0,0)`);
    g.addColorStop(1, `rgba(0,0,0,${strength})`);
    ctx.save();
    ctx.fillStyle = g;
    ctx.fillRect(0,0,w,h);
    ctx.restore();
  }

  // Exit highlight helper (call around your exit draw or after it with 'screen' comp)
  function drawExitGlow(ctx, cx, cy, tileSize){
    const ex = (window.MAZE_OPTS||{}).exit||{};
    const alpha = ex.glowAlpha==null ? 0.30 : ex.glowAlpha;
    const scale = ex.glowScale==null ? 1.15 : ex.glowScale;
    if (!ctx || !tileSize) return;
    const r = (tileSize * scale);
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
    g.addColorStop(0, 'rgba(255, 220, 60, 0.6)');
    g.addColorStop(1, 'rgba(255, 220, 60, 0.0)');
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    ctx.globalAlpha = alpha;
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI*2); ctx.fill();
    ctx.restore();
  }

  // Optional: calm the floor by drawing a subtle tint over the board AFTER floors.
  function floorTint(ctx, x, y, w, h){
    const f = (window.MAZE_OPTS||{}).floor||{};
    if (!ctx || !f.tint) return;
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = f.tint;
    ctx.fillRect(x,y,w,h);
    ctx.restore();
  }

  // Expose API
  window.installCanvasCrisp = installCanvasCrisp;
  window.computeNiceTileSize = computeNiceTileSize;
  window.touchupEndOfFrame = touchupEndOfFrame;
  window.drawExitGlow = drawExitGlow;
  window.floorTintOverlay = floorTint;
  window.snapPx = snapPx;
})();
