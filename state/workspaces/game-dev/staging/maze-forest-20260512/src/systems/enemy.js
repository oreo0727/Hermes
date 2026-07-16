(function(global){
  function los(grid, ax, ay, bx, by){
    if(ax===bx){ const [sy,ey] = ay<by?[ay,by]:[by,ay]; for(let y=sy+1;y<ey;y++){ if(grid[y][ax]===1) return false; } return true; }
    if(ay===by){ const [sx,ex] = ax<bx?[ax,bx]:[bx,ax]; for(let x=sx+1;x<ex;x++){ if(grid[ay][x]===1) return false; } return true; }
    return false;
  }
  function stepTowards(ax,ay,bx,by,grid){
    const opts=[]; if(ax<bx) opts.push([1,0]); if(ax>bx) opts.push([-1,0]); if(ay<by) opts.push([0,1]); if(ay>by) opts.push([0,-1]);
    for(let i=0;i<opts.length;i++){ const pair=opts[i]; if(!pair||pair.length<2) continue; const dx=pair[0], dy=pair[1]; const nx=ax+dx, ny=ay+dy; if(grid[ny] && grid[ny][nx]===0) return [nx,ny]; }
    return [ax,ay];
  }
  function randomStep(x,y,grid,rand){
    const dirs=[[1,0],[-1,0],[0,1],[0,-1]]; const pick = dirs[(rand()*dirs.length)|0];
    const nx=x+pick[0], ny=y+pick[1]; if(grid[ny] && grid[ny][nx]===0) return [nx,ny]; return [x,y];
  }
  function updateEnemies(state, rand){
    const g = state.level.grid; const p = state.player;
    for(let i=0;i<state.level.enemies.length;i++){
      const e = state.level.enemies[i];
      if(e.cooldown>0){ e.cooldown--; continue; }
      const see = los(g, e.x,e.y, p.x,p.y);
      if(see){ const step = stepTowards(e.x,e.y, p.x,p.y, g); e.x=step[0]; e.y=step[1]; }
      else { const step = randomStep(e.x,e.y, g, rand); e.x=step[0]; e.y=step[1]; }
      e.cooldown = 6; // slower than player
    }
  }
  global.Enemies = { updateEnemies };
})(window);
