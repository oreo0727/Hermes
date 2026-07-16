// Maze generator: recursive backtracker, BFS farthest exit, guarded addLoops
(function(){
  'use strict';
  const DIRS = [[1,0],[-1,0],[0,1],[0,-1]];

  function makeRNG(seed){ let s = (seed>>>0)||0x12345678; return function(){ s^=s<<13; s^=s>>>17; s^=s<<5; s>>>=0; return (s&0xffffffff)/0x100000000; }; }
  function shuffle(arr, rng){ const a=arr.slice(); for(let i=a.length-1;i>0;i--){ const j=(rng()* (i+1))|0; const t=a[i]; a[i]=a[j]; a[j]=t; } return a; }

  function inBounds(x,y,w,h){ return x>0 && y>0 && x<w-1 && y<h-1; }

  function carveMaze(w,h,rng){
    // odd dims grid: 1=wall, 0=floor
    const grid = Array.from({length:h}, (_,y)=>Array.from({length:w}, (_,x)=> 1));
    const startX = 1, startY = 1;
    function carve(x,y){
      grid[y][x] = 0;
      let dirs = shuffle([[2,0],[-2,0],[0,2],[0,-2]], rng);
      if(!Array.isArray(dirs)) dirs = [[2,0],[-2,0],[0,2],[0,-2]];
      for(let i=0;i<dirs.length;i++){
        const pair = dirs[i]; if(!pair || pair.length<2) continue;
        const dx = pair[0], dy = pair[1];
        const nx = x+dx, ny = y+dy;
        if(ny>0 && ny<h-1 && nx>0 && nx<w-1 && grid[ny][nx]===1){
          const mx = (x + (dx/2))|0, my=(y + (dy/2))|0; if(inBounds(mx,my,w,h)) grid[my][mx]=0;
          carve(nx,ny);
        }
      }
    }
    carve(startX,startY);
    return grid;
  }

  function farthestFrom(grid, sx, sy){
    const h=grid.length, w=grid[0].length;
    const dist = Array.from({length:h},()=>Array(w).fill(-1));
    const q=[[sx,sy]]; dist[sy][sx]=0; let best=[sx,sy,0];
    for(let qi=0; qi<q.length; qi++){
      const x=q[qi][0], y=q[qi][1]; const d=dist[y][x];
      for(let i=0;i<DIRS.length;i++){ const dx=DIRS[i][0], dy=DIRS[i][1]; const nx=x+dx, ny=y+dy;
        if(ny>=0&&ny<h&&nx>=0&&nx<w && grid[ny][nx]===0 && dist[ny][nx]===-1){ dist[ny][nx]=d+1; q.push([nx,ny]); if(d+1>best[2]) best=[nx,ny,d+1]; }
      }
    }
    return {x:best[0], y:best[1], d:best[2]};
  }

  function addLoops(grid, attempts, rng){
    // Guarded: never throws; only opens interior walls with >=2 floor neighbors
    if(!grid || !grid.length || !grid[0]) return 0;
    const h=grid.length, w=grid[0].length; let added=0;
    const isWall=(x,y)=> grid[y] && grid[y][x]===1;
    const isFloor=(x,y)=> grid[y] && grid[y][x]===0;
    const candidates=[];
    for(let y=2; y<h-2; y++){
      for(let x=2; x<w-2; x++){
        if(isWall(x,y)){
          let floors=0;
          for(let i=0;i<DIRS.length;i++){ const dx=DIRS[i][0], dy=DIRS[i][1]; if(isFloor(x+dx,y+dy)) floors++; }
          if(floors>=2) candidates.push([x,y]);
        }
      }
    }
    if(!candidates.length) return 0;
    const order = shuffle(candidates, rng);
    const max = Math.min(order.length, Math.max(0, attempts|0));
    for(let i=0;i<max;i++){
      const p=order[i]; if(!p||p.length<2) continue; const x=p[0], y=p[1];
      if(x<=0||y<=0||x>=w-1||y>=h-1) continue;
      // Open single wall cell if it still looks like a good loop
      let floors=0; for(let k=0;k<DIRS.length;k++){ const dx=DIRS[k][0], dy=DIRS[k][1]; if(isFloor(x+dx,y+dy)) floors++; }
      if(floors>=2 && grid[y][x]===1){ grid[y][x]=0; added++; }
    }
    return added;
  }

  function sizeForLevel(level){ const base=15; const inc = Math.min(18, (level-1)*2); let n = base+inc; if(n%2===0) n++; return Math.min(n, 51)|0; }
  function loopAttemptsFor(level){ return Math.min( Math.floor(level*1.5), 60); }

  function generateLevel(level, seed){
    const rng = makeRNG((seed||Date.now()) ^ (level*9301));
    const n = sizeForLevel(level);
    const grid = carveMaze(n,n,rng);
    const start = {x:1,y:1};
    const far = farthestFrom(grid, start.x, start.y);
    const exit = {x:far.x, y:far.y};
    try{ addLoops(grid, loopAttemptsFor(level), rng); }
    catch(e){ console.warn('addLoops failed; continuing without loops', e); }
    return { grid, start, exit, seedUsed: seed||0 };
  }

  window.MazeGen = { generateLevel, sizeForLevel };
  console.log('MazeGen: generator.js v1 loaded');
})();
