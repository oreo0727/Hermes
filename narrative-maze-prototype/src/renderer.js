(function(){
  function cssVar(name, fallback){
    try{ const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim(); return v || fallback; }catch(_){ return fallback; }
  }

  function roundedRect(ctx, x,y,w,h,r){
    if(r<=0){ ctx.rect(x,y,w,h); return; }
    ctx.beginPath();
    ctx.moveTo(x+r, y);
    ctx.arcTo(x+w, y,   x+w, y+h, r);
    ctx.arcTo(x+w, y+h, x,   y+h, r);
    ctx.arcTo(x,   y+h, x,   y,   r);
    ctx.arcTo(x,   y,   x+w, y,   r);
    ctx.closePath();
  }

  function render(ctx, state){
    const W = ctx.canvas.width, H = ctx.canvas.height;
    ctx.clearRect(0,0,W,H);

    const level = state.level;
    const grid = level && level.grid;
    if(!grid || !grid.length || !grid[0]){
      // canvas probe and guard
      ctx.fillStyle = '#0b1d12'; ctx.fillRect(0,0,W,H);
      if (window && window.MF_DEBUG) { ctx.fillStyle = '#ff00ff'; ctx.fillRect(8,8,8,8); }
      return { ts: 0, ox: 0, oy: 0 };
    }

    const rows = grid.length, cols = grid[0].length;
    let ts = Math.floor(Math.min(W/cols, H/rows));
    // bias to even sizes to reduce antialiasing, and prefer ~64px when close
    const candidates = [64, 56, 48, 40, 32, 24, 16];
    for(let i=0;i<candidates.length;i++){
      const cand = Math.floor(Math.min(W/cols, H/rows));
      // if the current size is within 10% of a nicer canonical size, snap
      if(Math.abs(ts - candidates[i]) <= candidates[i]*0.1){ ts = candidates[i]; break; }
    }
    if(!ts) ts = 8; // clamp small but visible
    const mapW = cols*ts, mapH = rows*ts;

    // center map
    const ox = Math.floor((W - mapW)/2);
    const oy = Math.floor((H - mapH)/2);

    // Background (deep forest)
    const bgDark = cssVar('--forest-dark', '#0d2b19');
    ctx.fillStyle = bgDark; ctx.fillRect(0,0,W,H);

    // Colors
    const soil = cssVar('--soil', '#6f5434');
    const soil2 = '#8a6a3e';
    const stone = cssVar('--stone', '#6a755f');
    const stoneAlt = '#596756';
    const moss = cssVar('--moss', '#89c25a');
    const exitGlow = cssVar('--exitGlow', '#fff1a8');
    const storyCol = cssVar('--purple-magic', '#9a57ff');

    // Draw tiles
    for(let r=0;r<rows;r++){
      for(let c=0;c<cols;c++){
        const x = ox + c*ts, y = oy + r*ts;
        const v = grid[r][c];
        if(v===0){ // wall: rounded stone block with moss and soft shadow
          // drop shadow onto path
          ctx.save();
          ctx.shadowColor = 'rgba(0,0,0,0.35)';
          ctx.shadowBlur = Math.max(8, ts*0.25);
          ctx.shadowOffsetY = Math.max(4, ts*0.12);
          ctx.fillStyle = ((r+c)&1)? stone : stoneAlt;
          roundedRect(ctx, x+1, y+1, ts-2, ts-2, Math.max(6, ts*0.12));
          ctx.fill();
          ctx.restore();

          // top highlight + bottom shadow bevel
          ctx.fillStyle = 'rgba(255,255,255,0.08)';
          ctx.fillRect(x+2, y+2, ts-4, Math.max(1, ts*0.08));
          ctx.fillStyle = 'rgba(0,0,0,0.15)';
          ctx.fillRect(x+2, y+ts-Math.max(2, ts*0.12), ts-4, Math.max(2, ts*0.12));

          // moss speckles
          ctx.globalAlpha = 0.25; ctx.fillStyle = moss;
          const dots = 3; const dsz = Math.max(1, ts*0.06)|0;
          for(let i=0;i<dots;i++) ctx.fillRect(x+2+(i*dsz*2)% (ts-4), y+2+((i*7)% (ts-4)), dsz, dsz);
          ctx.globalAlpha = 1;
        } else { // floor or exit background soil
          const col = ((r+c)&1)? soil : soil2;
          ctx.fillStyle = col; ctx.fillRect(x,y,ts,ts);

          if(v===2){ // exit: inner stroke + radial glow
            // thin inner ring
            ctx.strokeStyle = exitGlow; ctx.lineWidth = Math.max(1, ts/10);
            ctx.strokeRect(x+Math.max(2,ts*0.1), y+Math.max(2,ts*0.1), ts-Math.max(4,ts*0.2), ts-Math.max(4,ts*0.2));
            // glow
            const rg = ctx.createRadialGradient(x+ts/2, y+ts/2, ts*0.15, x+ts/2, y+ts/2, ts*0.75);
            rg.addColorStop(0, exitGlow);
            rg.addColorStop(1, 'rgba(255,241,168,0)');
            ctx.fillStyle = rg; ctx.globalCompositeOperation = 'lighter';
            ctx.fillRect(x-ts*0.2, y-ts*0.2, ts*1.4, ts*1.4);
            ctx.globalCompositeOperation = 'source-over';
          }
        }
      }
    }

    // Story nodes: crystal with additive glow
    if(level.storyNodes){
      for(let i=0;i<level.storyNodes.length;i++){
        const sn = level.storyNodes[i];
        const x = ox + sn.c*ts, y = oy + sn.r*ts;
        const pad = Math.max(3, ts*0.18|0);
        const cx = x+ts/2, cy = y+ts/2;
        // glow
        const pg = ctx.createRadialGradient(cx, cy, ts*0.05, cx, cy, ts*0.6);
        pg.addColorStop(0, storyCol);
        pg.addColorStop(1, 'rgba(154,87,255,0)');
        ctx.globalCompositeOperation = 'lighter';
        ctx.fillStyle = pg; ctx.fillRect(x-pad, y-pad, ts+pad*2, ts+pad*2);
        ctx.globalCompositeOperation = 'source-over';
        // core diamond
        ctx.fillStyle = storyCol; ctx.globalAlpha = 0.9;
        ctx.beginPath();
        ctx.moveTo(cx, y+pad);
        ctx.lineTo(x+ts-pad, cy);
        ctx.lineTo(cx, y+ts-pad);
        ctx.lineTo(x+pad, cy);
        ctx.closePath();
        ctx.fill();
        ctx.globalAlpha = 1;
      }
    }

    // Player: rounded square with soft shadow
    const p = state.player;
    if(p){
      const x = ox + p.c*ts, y = oy + p.r*ts;
      const rad = Math.max(4, ts*0.2);
      // shadow
      ctx.save();
      ctx.shadowColor = 'rgba(0,0,0,0.55)';
      ctx.shadowBlur = Math.max(4, ts*0.2);
      ctx.shadowOffsetY = Math.max(2, ts*0.1);
      ctx.fillStyle = cssVar('--blue-ui', '#10a1ff');
      roundedRect(ctx, x+2, y+2, ts-4, ts-4, rad);
      ctx.fill();
      ctx.restore();
      // inner highlight
      ctx.strokeStyle = 'rgba(255,255,255,0.25)';
      ctx.lineWidth = Math.max(1, ts*0.05);
      ctx.strokeRect(x+3, y+3, ts-6, ts-6);
    }

    // Vignette overlay
    const vg = ctx.createRadialGradient(W/2,H/2, Math.min(W,H)*0.45, W/2,H/2, Math.min(W,H)*0.9);
    vg.addColorStop(0, 'rgba(0,0,0,0)');
    vg.addColorStop(1, 'rgba(0,0,0,0.5)');
    ctx.fillStyle = vg; ctx.fillRect(0,0,W,H);

    // Probe (debug only)
    if (window && window.MF_DEBUG) { ctx.fillStyle = '#ff00ff'; ctx.fillRect(8,8,8,8); }

    return { ts, ox, oy };
  }

  window.Renderer = { render };
})();
