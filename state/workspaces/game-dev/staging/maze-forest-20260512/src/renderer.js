(function(global){
  function cssVar(name, fallback){
    try{ const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim(); return v || fallback; }catch(_){ return fallback; }
  }
  function roundedRect(ctx,x,y,w,h,r){ const rr=Math.min(r,w/2,h/2); ctx.beginPath(); ctx.moveTo(x+rr,y); ctx.arcTo(x+w,y,x+w,y+h,rr); ctx.arcTo(x+w,y+h,x,y+h,rr); ctx.arcTo(x,y+h,x,y,rr); ctx.arcTo(x,y,x+w,y,rr); ctx.closePath(); }

  function render(state, ctx, W, H){
    // Backdrop so canvas is never fully blank
    ctx.fillStyle = cssVar('--forest-dark','#0d2b19');
    ctx.fillRect(0,0,W,H);
    // Visible probe in debug
    try{ if(window.MF_DEBUG){ ctx.fillStyle = '#ff00ff'; ctx.fillRect(8,8,8,8); } }catch(_){ }

    const level = state && state.level; const grid = level && level.grid;
    if(!grid || !grid.length || !grid[0]){ return {ts:0, ox:0, oy:0}; }
    const rows = grid.length, cols = grid[0].length;

    let ts = Math.floor(Math.min(W/cols, H/rows));
    const nice = [96,88,80,72,64,56,48,40,32,24,16,12,8];
    for (let i=0;i<nice.length;i++){ if (Math.abs(ts-nice[i]) <= Math.max(2, (nice[i]*0.1)|0)){ ts = nice[i]; break; } }
    if(!ts) ts = 8;
    const ox = Math.floor((W - cols*ts)/2), oy = Math.floor((H - rows*ts)/2);
    try{ console.debug(`Renderer debug: rows=${rows} cols=${cols} ts=${ts} canvas=${W}x${H}`); }catch(_){ }

    // Tiles
    for(let r=0;r<rows;r++){
      for(let c=0;c<cols;c++){
        const x = ox + c*ts, y = oy + r*ts;
        if(grid[r][c]===1){
          // Stone wall block with bevel/moss
          ctx.save();
          ctx.shadowColor='rgba(0,0,0,0.35)'; ctx.shadowBlur=Math.max(8, ts*0.25); ctx.shadowOffsetY=Math.max(4, ts*0.12);
          ctx.fillStyle = ((r+c)&1)? cssVar('--stone','#6a755f') : '#596756';
          roundedRect(ctx, x+1, y+1, ts-2, ts-2, Math.max(6, ts*0.12)); ctx.fill();
          ctx.restore();
          // bevel highlights
          ctx.fillStyle='rgba(255,255,255,0.08)'; ctx.fillRect(x+2,y+2, ts-4, Math.max(1, ts*0.08));
          ctx.fillStyle='rgba(0,0,0,0.15)'; ctx.fillRect(x+2, y+ts-Math.max(2, ts*0.12), ts-4, Math.max(2, ts*0.12));
          // moss flecks
          ctx.globalAlpha=0.25; ctx.fillStyle=cssVar('--moss','#89c25a'); const d=Math.max(1, ts*0.06)|0; for(let i=0;i<3;i++){ ctx.fillRect(x+2+(i*d*2)%(ts-4), y+2+((i*7)%(ts-4)), d, d); } ctx.globalAlpha=1;
        } else {
          // Warm soil floor
          const soil = cssVar('--soil','#6f5434'); const soil2 = '#8a6a3e';
          ctx.fillStyle = ((r+c)&1)? soil : soil2; ctx.fillRect(x,y,ts,ts);
        }
      }
    }

    // Exit portal glow + ring (level.exit)
    if(level && level.exit){
      const ex=level.exit.x, ey=level.exit.y; const x=ox+ex*ts, y=oy+ey*ts;
      ctx.strokeStyle = cssVar('--exitGlow','#fff1a8'); ctx.lineWidth = Math.max(1, ts/10);
      ctx.strokeRect(x+Math.max(2,ts*0.1), y+Math.max(2,ts*0.1), ts-Math.max(4,ts*0.2), ts-Math.max(4,ts*0.2));
      const rg = ctx.createRadialGradient(x+ts/2,y+ts/2, ts*0.15, x+ts/2,y+ts/2, ts*0.75);
      rg.addColorStop(0, cssVar('--exitGlow','#fff1a8')); rg.addColorStop(1, 'rgba(255,241,168,0)');
      ctx.globalCompositeOperation='lighter'; ctx.fillStyle=rg; ctx.fillRect(x-ts*0.2, y-ts*0.2, ts*1.4, ts*1.4);
      ctx.globalCompositeOperation='source-over';
    }

    // Traps
    if(level && Array.isArray(level.traps)){
      for(let i=0;i<level.traps.length;i++){
        const t=level.traps[i]; const x=ox+t.x*ts, y=oy+t.y*ts; const active=((state.ticks+(t.phase||0))%60)<30;
        ctx.save(); ctx.translate(x+ts/2, y+ts/2); ctx.rotate(Math.PI/4);
        ctx.shadowColor='rgba(0,0,0,0.35)'; ctx.shadowBlur=Math.max(4, ts*0.15); ctx.shadowOffsetY=Math.max(1, ts*0.08);
        ctx.fillStyle = active ? 'rgba(199,165,107,0.95)' : 'rgba(199,165,107,0.45)';
        roundedRect(ctx, -ts*0.33, -ts*0.33, ts*0.66, ts*0.66, Math.max(3, ts*0.14)); ctx.fill();
        ctx.restore();
      }
    }

    // Power-ups
    if(level && Array.isArray(level.powerups)){
      for(let i=0;i<level.powerups.length;i++){
        const p=level.powerups[i]; const x=ox+p.x*ts, y=oy+p.y*ts; const cx=x+ts/2, cy=y+ts/2;
        let col = '#83c8f1'; if(p.kind==='heal') col='#8ef0a8'; else if(p.kind==='shield') col='#9bbcf7';
        const pg = ctx.createRadialGradient(cx,cy, ts*0.05, cx,cy, ts*0.6); pg.addColorStop(0, col); pg.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.globalCompositeOperation='lighter'; ctx.fillStyle=pg; ctx.fillRect(x-ts*0.2,y-ts*0.2,ts*1.4,ts*1.4);
        ctx.globalCompositeOperation='source-over';
        ctx.save(); ctx.shadowColor='rgba(0,0,0,0.35)'; ctx.shadowBlur=Math.max(3, ts*0.14); ctx.shadowOffsetY=Math.max(1, ts*0.09);
        ctx.fillStyle = col; roundedRect(ctx, x+ts*0.13, y+ts*0.13, ts*0.74, ts*0.74, Math.max(4, ts*0.2)); ctx.fill(); ctx.restore();
      }
    }

    // Enemies
    if(level && Array.isArray(level.enemies)){
      for(let i=0;i<level.enemies.length;i++){
        const e=level.enemies[i]; const x=ox+e.x*ts, y=oy+e.y*ts;
        ctx.save(); ctx.shadowColor='rgba(0,0,0,0.45)'; ctx.shadowBlur=Math.max(4, ts*0.2); ctx.shadowOffsetY=Math.max(2, ts*0.11);
        ctx.fillStyle = cssVar('--red','#ff4a4a'); roundedRect(ctx, x+ts*0.09, y+ts*0.09, ts*0.82, ts*0.82, Math.max(5, ts*0.24)); ctx.fill();
        ctx.restore();
        ctx.strokeStyle='rgba(0,0,0,0.25)'; ctx.lineWidth=Math.max(1, ts*0.05); ctx.strokeRect(x+ts*0.12, y+ts*0.12, ts*0.76, ts*0.76);
      }
    }

    // Player
    if(state && state.player){
      const x=ox+state.player.x*ts, y=oy+state.player.y*ts;
      ctx.save(); ctx.shadowColor='rgba(0,0,0,0.55)'; ctx.shadowBlur=Math.max(4, ts*0.22); ctx.shadowOffsetY=Math.max(2, ts*0.12);
      ctx.fillStyle = cssVar('--blue-ui','#10a1ff'); roundedRect(ctx, x+ts*0.02,y+ts*0.02, ts*0.96, ts*0.96, Math.max(4, ts*0.22)); ctx.fill(); ctx.restore();
      ctx.strokeStyle='rgba(255,255,255,0.25)'; ctx.lineWidth=Math.max(1, ts*0.05); ctx.strokeRect(x+ts*0.04,y+ts*0.04, ts*0.92, ts*0.92);
    }

    // Soft vignette
    const vg = ctx.createRadialGradient(W/2,H/2, Math.min(W,H)*0.45, W/2,H/2, Math.min(W,H)*0.9);
    vg.addColorStop(0,'rgba(0,0,0,0)'); vg.addColorStop(1,'rgba(0,0,0,0.5)');
    ctx.fillStyle = vg; ctx.fillRect(0,0,W,H);

    return {ts, ox, oy};
  }

  global.Renderer = { render };
})(window);
