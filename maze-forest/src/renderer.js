(function(global){
  // Cozy renderer with safe fallbacks and visible probe
  function cssVar(name, fallback){
    try{ const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim(); return v || fallback; }
    catch(_){ return fallback; }
  }
  function drawRoundedRect(ctx,x,y,w,h,r){
    const rr = Math.min(r, w/2, h/2);
    ctx.beginPath();
    ctx.moveTo(x+rr,y); ctx.arcTo(x+w,y,x+w,y+h,rr); ctx.arcTo(x+w,y+h,x,y+h,rr);
    ctx.arcTo(x,y+h,x,y,rr); ctx.arcTo(x,y,x+w,y,rr); ctx.closePath();
  }

  function render(state, ctx, W, H){
    const level = state && state.level;
    const grid = level && level.grid; if(!grid || !grid.length || !grid[0]){
      // Visibly initialize so page isn't blank
      ctx.fillStyle = cssVar('--forest-dark', '#0d2b19'); ctx.fillRect(0,0,W,H);
      // Probe to confirm paint path (debug only)
      if (window && window.MF_DEBUG) { ctx.fillStyle = '#ff00ff'; ctx.fillRect(8,8,8,8); }
      return {ts:0,ox:0,oy:0};
    }
    const rows = grid.length, cols = grid[0].length;
    let ts = Math.floor(Math.min(W/cols, H/rows));
    if(!ts || !isFinite(ts)) ts = 8; // clamp
    // Snap to nice sizes for crisp edges when close
    const nice=[96,88,80,72,64,56,48,40,32,24,16,12,8];
    for(let i=0;i<nice.length;i++){ if(Math.abs(ts-nice[i]) <= Math.max(2, nice[i]*0.1)) { ts = nice[i]; break; } }
    const ox = Math.floor((W - cols*ts)/2), oy = Math.floor((H - rows*ts)/2);

    // Backdrop
    ctx.fillStyle = cssVar('--forest-dark', '#0d2b19');
    ctx.fillRect(0,0,W,H);

    // Tiles: 1=wall, 0=floor (Maze Forest semantics)
    const soil = cssVar('--soil', '#6f5434');
    const soil2 = '#8a6a3e';
    const stone1 = cssVar('--stone', '#6a755f');
    const stone2 = '#596756';

    const disableSprites = (function(){ try { return (localStorage.getItem('mf_no_sprites')||'')==='1'; } catch(_) { return false; } })();
    const useSprites = !!(!disableSprites && window.SPRITES_READY && window.drawSprite);

    for(let r=0;r<rows;r++){
      for(let c=0;c<cols;c++){
        const x = ox + c*ts, y = oy + r*ts;
        if(grid[r][c]===1){
          // Walls
          let drawn = false;
          if(useSprites){
            drawn = drawSprite(ctx, 'terrain/wall-top-n', x, y, ts, {center:false});
          }
          if(!drawn){
            const fill = ((r+c)&1) ? stone1 : stone2;
            ctx.save();
            ctx.shadowColor='rgba(0,0,0,0.35)'; ctx.shadowBlur=Math.max(8, ts*0.25); ctx.shadowOffsetY=Math.max(2, ts*0.12);
            ctx.fillStyle = fill; drawRoundedRect(ctx, x+1, y+1, ts-2, ts-2, Math.max(4, ts*0.18)); ctx.fill();
            ctx.restore();
            ctx.fillStyle='rgba(255,255,255,0.08)'; ctx.fillRect(x+2,y+2, ts-4, Math.max(1, ts*0.08));
          }
        } else {
          // Floors
          let drawn = false;
          if(useSprites){
            const v = ((c*73856093 ^ r*19349663) >>> 0) % 4 + 1;
            drawn = drawSprite(ctx, `terrain/floor-dirt-var${v}`, x, y, ts, {center:false});
            // Optional tiny decals for charm (low probability)
            if(drawn){
              const rnd = ((c*83492791 ^ r*2971215073) >>> 0) % 32;
              const decal = rnd===0? 'terrain/decals-pebble' : rnd===1? 'terrain/decals-fern' : rnd===2? 'terrain/decals-flower-blue' : rnd===3? 'terrain/decals-flower-red' : rnd===4? 'terrain/decals-mushroom' : null;
              if(decal) drawSprite(ctx, decal, x, y, ts*0.6, {center:false});
            }
          }
          if(!drawn){
            ctx.fillStyle = ((c*73856093 ^ r*19349663) & 8) ? soil : soil2;
            ctx.fillRect(x,y,ts,ts);
          }
        }
      }
    }

    // Exit (door or glow fallback)
    const ex = level.exit.x, ey = level.exit.y;
    const exx = ox + ex*ts, exy = oy + ey*ts;
    let exitDrawn = false;
    if(useSprites){ exitDrawn = drawSprite(ctx, 'terrain/door-exit-open', exx, exy, ts, {center:false, w: ts*2, h: ts*2}); }
    if(!exitDrawn){
      const cx = exx + ts/2, cy = exy + ts/2;
      const glow = ctx.createRadialGradient(cx,cy, ts*0.1, cx,cy, ts*0.8);
      glow.addColorStop(0, cssVar('--exitGlow','#fff1a8'));
      glow.addColorStop(1, 'rgba(255,241,168,0)');
      ctx.globalCompositeOperation='lighter'; ctx.fillStyle=glow; ctx.fillRect(cx-ts, cy-ts, ts*2, ts*2);
      ctx.globalCompositeOperation='source-over';
      ctx.fillStyle = cssVar('--exit', '#a6f2c1'); drawRoundedRect(ctx, cx-ts*0.3, cy-ts*0.3, ts*0.6, ts*0.6, Math.max(4, ts*0.18)); ctx.fill();
    }

    // Traps (spikes plate anim)
    if(level.traps && level.traps.length){
      for(let i=0;i<level.traps.length;i++){
        const t = level.traps[i]; const x = ox + t.x*ts, y = oy + t.y*ts;
        let drawn=false;
        if(useSprites){ const fi = Math.floor((state.ticks/6))%4; drawn = drawSprite(ctx, 'hazards/spikes-plate-1', x, y, ts, {frameIndex:fi}); }
        if(!drawn){
          const active = ((state.ticks + (t.phase||0)) % 60) < 30;
          ctx.save(); ctx.translate(x+ts/2, y+ts/2); ctx.rotate(Math.PI/4);
          ctx.fillStyle = active ? 'rgba(199,165,107,0.95)' : 'rgba(199,165,107,0.45)';
          drawRoundedRect(ctx, -ts*0.33, -ts*0.33, ts*0.66, ts*0.66, Math.max(3, ts*0.14)); ctx.fill();
          ctx.restore();
        }
      }
    }

    // Power-ups
    if(level.powerups && level.powerups.length){
      for(let i=0;i<level.powerups.length;i++){
        const p = level.powerups[i]; const x = ox + p.x*ts, y = oy + p.y*ts;
        let drawn=false;
        if(useSprites){
          if(p.kind==='heal') { const fi=Math.floor(state.ticks/8)%4; drawn = drawSprite(ctx,'pickups/potion-red-1',x,y,ts,{frameIndex:fi}); }
          else if(p.kind==='shield'){ const fi=Math.floor(state.ticks/8)%4; drawn = drawSprite(ctx,'pickups/shield-blue-1',x,y,ts,{frameIndex:fi}); }
          else if(p.kind==='speed'){ const fi=Math.floor(state.ticks/6)%3; drawn = drawSprite(ctx,'pickups/tile-lightning-1',x,y,ts,{frameIndex:fi}); }
        }
        if(!drawn){
          const k = p.kind; let col = '#83c8f1';
          if(k==='heal') col = '#8ef0a8'; else if(k==='shield') col = '#9bbcf7';
          const rg = ctx.createRadialGradient(x+ts/2,y+ts/2, ts*0.05, x+ts/2,y+ts/2, ts*0.6);
          rg.addColorStop(0, col); rg.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.globalCompositeOperation='lighter'; ctx.fillStyle=rg; ctx.fillRect(x-ts*0.2,y-ts*0.2,ts*1.4,ts*1.4);
          ctx.globalCompositeOperation='source-over';
          ctx.save(); ctx.shadowColor='rgba(0,0,0,0.35)'; ctx.shadowBlur=Math.max(3, ts*0.14); ctx.shadowOffsetY=Math.max(1, ts*0.09);
          ctx.fillStyle = col; drawRoundedRect(ctx, x+ts*0.13, y+ts*0.13, ts*0.74, ts*0.74, Math.max(4, ts*0.2)); ctx.fill(); ctx.restore();
        }
      }
    }

    // Enemies (use skeleton walk as default)
    if(level.enemies && level.enemies.length){
      for(let i=0;i<level.enemies.length;i++){
        const e = level.enemies[i]; const x = ox + e.x*ts, y = oy + e.y*ts;
        let drawn=false;
        if(useSprites){ const fi = Math.floor(state.ticks/8)%4; drawn = drawSprite(ctx,'enemies/skeleton-walk-1', x, y, ts, {frameIndex:fi}); }
        if(!drawn){
          ctx.save(); ctx.shadowColor='rgba(0,0,0,0.45)'; ctx.shadowBlur=Math.max(4, ts*0.2); ctx.shadowOffsetY=Math.max(2, ts*0.11);
          ctx.fillStyle = cssVar('--red', '#ff4a4a'); drawRoundedRect(ctx, x+ts*0.09, y+ts*0.09, ts*0.82, ts*0.82, Math.max(5, ts*0.24)); ctx.fill();
          ctx.restore();
          ctx.strokeStyle='rgba(0,0,0,0.25)'; ctx.lineWidth=Math.max(1, ts*0.05); ctx.strokeRect(x+ts*0.12, y+ts*0.12, ts*0.76, ts*0.76);
        }
      }
    }

    // Player
    const px = ox + state.player.x*ts, py = oy + state.player.y*ts;
    let playerDrawn=false;
    if(useSprites){ const fi=Math.floor(state.ticks/8)%4; playerDrawn = drawSprite(ctx,'player/hero-walk-1', px, py, ts, {frameIndex:fi}); }
    if(!playerDrawn){
      ctx.save(); ctx.shadowColor='rgba(0,0,0,0.55)'; ctx.shadowBlur=Math.max(4, ts*0.22); ctx.shadowOffsetY=Math.max(2, ts*0.12);
      ctx.fillStyle = cssVar('--blue-ui', '#10a1ff'); drawRoundedRect(ctx, px+ts*0.02,py+ts*0.02, ts*0.96, ts*0.96, Math.max(4, ts*0.22)); ctx.fill(); ctx.restore();
      ctx.strokeStyle='rgba(255,255,255,0.25)'; ctx.lineWidth=Math.max(1, ts*0.05); ctx.strokeRect(px+ts*0.04,py+ts*0.04, ts*0.92, ts*0.92);
    }

    // Soft vignette framing
    const vg = ctx.createRadialGradient(W/2,H/2, Math.min(W,H)*0.45, W/2,H/2, Math.min(W,H)*0.9);
    vg.addColorStop(0,'rgba(0,0,0,0)'); vg.addColorStop(1,'rgba(0,0,0,0.4)');
    ctx.fillStyle = vg; ctx.fillRect(0,0,W,H);

    // Debug corner probe
    if (window && window.MF_DEBUG) { ctx.fillStyle = '#ff00ff'; ctx.fillRect(8,8,8,8); }

    return {ts, ox, oy};
  }

  global.Renderer = { render };
})(window);
