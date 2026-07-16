(function(){
  'use strict';
  function cssVar(name, fallback){ try{ const v=getComputedStyle(document.documentElement).getPropertyValue(name).trim(); return v||fallback; }catch(_){ return fallback; } }

  function render(state, ctx, w, h){
    const level = state.level; const grid = level && level.grid; if(!grid || !grid.length || !grid[0]){ return {ts:0,ox:0,oy:0}; }
    const rows = grid.length, cols = grid[0].length;
    let ts = Math.floor(Math.min(w/cols, h/rows)); if(!ts) ts = 6; // clamp
    // snap to crisp integer coords
    const ox = Math.floor((w - cols*ts)/2), oy = Math.floor((h - rows*ts)/2);

    // clear + vignette base
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle = cssVar('--soil1', '#5b4429'); ctx.fillRect(0,0,w,h);
    // canvas probe
    ctx.fillStyle = '#ff00ff'; ctx.fillRect(8,8,8,8);

    // draw grid
    for(let y=0;y<rows;y++){
      for(let x=0;x<cols;x++){
        const v = grid[y][x];
        const px = ox + x*ts, py = oy + y*ts;
        if(v===1){ // wall
          ctx.fillStyle = cssVar('--stone', '#3b4a3f');
          ctx.fillRect(px,py,ts,ts);
          ctx.fillStyle = cssVar('--moss', '#496a55');
          ctx.globalAlpha = 0.25; ctx.fillRect(px+1,py+1,ts-2,Math.max(1, (ts*0.3)|0)); ctx.globalAlpha=1;
        } else { // floor or exit
          ctx.fillStyle = cssVar('--soil2', '#7a5530');
          ctx.fillRect(px,py,ts,ts);
        }
      }
    }

    // exit
    if(level.exit){ const ex = ox + level.exit.x*ts, ey = oy + level.exit.y*ts; ctx.strokeStyle = cssVar('--exit','#ffd36a'); ctx.lineWidth = Math.max(1, (ts*0.12)|0); ctx.strokeRect(ex+2,ey+2,ts-4,ts-4);
      // subtle glow
      const r = ts*0.9; const g=ctx.createRadialGradient(ex+ts/2,ey+ts/2, ts*0.1, ex+ts/2,ey+ts/2, r);
      g.addColorStop(0, 'rgba(255,210,106,0.35)'); g.addColorStop(1,'rgba(255,210,106,0)');
      ctx.fillStyle=g; ctx.beginPath(); ctx.arc(ex+ts/2,ey+ts/2,r,0,Math.PI*2); ctx.fill(); }

    // entities
    const ents = state.entities||[];
    for(let i=0;i<ents.length;i++){
      const e = ents[i]; const px = ox + e.x*ts, py = oy + e.y*ts; const m = Math.max(2, (ts*0.12)|0);
      if(e.type==='player'){ ctx.fillStyle = cssVar('--player','#5aa7ff'); ctx.fillRect(px+m,py+m,ts-2*m,ts-2*m); }
      else if(e.type==='enemy'){ ctx.fillStyle = cssVar('--enemy','#e25555'); ctx.fillRect(px+m,py+m,ts-2*m,ts-2*m); }
      else if(e.type==='trap'){
        const on = ((state.tick + (e.phase||0)) % (e.period||60)) < ((e.period||60)/2);
        ctx.fillStyle = on? cssVar('--trap','#b377ff') : 'rgba(179,119,255,0.35)';
        // diamond
        ctx.beginPath(); ctx.moveTo(px+ts/2,py+m); ctx.lineTo(px+ts-m,py+ts/2); ctx.lineTo(px+ts/2,py+ts-m); ctx.lineTo(px+m,py+ts/2); ctx.closePath(); ctx.fill();
      } else if(e.type==='power'){
        ctx.fillStyle = cssVar('--power','#ffd166'); ctx.globalAlpha=0.9; ctx.fillRect(px+m,py+m,ts-2*m,ts-2*m); ctx.globalAlpha=1;
      }
    }

    return {ts,ox,oy};
  }

  window.Renderer = { render };
})();
