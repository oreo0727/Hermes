// Maze + level generator
// Guarantees solvable path. Adds loops and hazards by level.

(function(global){
  const DIRS = [ [1,0],[-1,0],[0,1],[0,-1] ];
  console.log('MazeGen: generator.js v5 loaded');

  function randChoice(arr, rng){ return arr[(rng() * arr.length)|0]; }

  function makeRNG(seed){
    let s = seed >>> 0 || 123456789;
    return function(){
      // xorshift32
      s ^= s << 13; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return (s & 0xffffffff) / 0x100000000;
    };
  }

  function inBounds(x,y,w,h){ return x>=0 && y>=0 && x<w && y<h; }

  function shuffle(a, rng){ for(let i=a.length-1;i>0;--i){ const j=(rng()* (i+1))|0; [a[i],a[j]]=[a[j],a[i]]; } return a; }

  // Create odd-sized grid for clean walls between paths
  function sizeForLevel(level){
    const base = 15; // cozy small start
    const inc = Math.min(18, Math.floor(level/2)*2 + (level%2?1:0));
    let n = base + inc; if(n % 2 === 0) n += 1; return Math.min(n, 51); // perf cap
  }

  function carveMaze(w,h,rng){
    // grid: 1 = wall, 0 = floor
    const grid = Array.from({length:h},()=>Array(w).fill(1));
    // start at (1,1)
    function carve(x,y){
      grid[y][x]=0;
      let dirs = shuffle([[2,0],[-2,0],[0,2],[0,-2]], rng);
      if(!Array.isArray(dirs)) dirs = [[2,0],[-2,0],[0,2],[0,-2]];
      for(let i=0;i<dirs.length;i++){
        const pair = dirs[i]; if(!pair || pair.length<2) continue;
        const dx = pair[0], dy = pair[1];
        const nx=x+dx, ny=y+dy;
        if(ny>0 && ny<h-1 && nx>0 && nx<w-1 && grid[ny][nx]===1){ grid[(y + (dy/2))|0][(x + (dx/2))|0]=0; carve(nx,ny);}
      }
    }
    carve(1,1);
    return grid;
  }

  function addLoops(grid, loops, rng){
    const h=grid.length,w=grid[0].length; let added=0, attempts=0;
    while(added<loops && attempts<loops*20){ attempts++;
      const x = 2+((rng()* (w-4))|0); const y = 2+((rng()* (h-4))|0);
      if(grid[y][x]===1){ // open a wall if it's between two floors
        let floors=0; for(const [dx,dy] of DIRS){ const nx=x+dx,ny=y+dy; if(inBounds(nx,ny,w,h) && grid[ny][nx]===0) floors++; }
        if(floors>=2){ grid[y][x]=0; added++; }
      }
    }
  }

  function farthestFrom(grid, sx, sy){
    const h=grid.length,w=grid[0].length; const q=[[sx,sy,0]]; const seen=new Set([sx+","+sy]);
    let best=[sx,sy,0];
    while(q.length){ const item=q.shift(); const x=item[0], y=item[1], d=item[2]; if(d>best[2]) best=[x,y,d];
      for(let i=0;i<DIRS.length;i++){ const dx=DIRS[i][0], dy=DIRS[i][1]; const nx=x+dx, ny=y+dy; const k=nx+","+ny; if(inBounds(nx,ny,w,h) && grid[ny][nx]===0 && !seen.has(k)){ seen.add(k); q.push([nx,ny,d+1]); } }
    }
    return {x:best[0], y:best[1], dist:best[2]};
  }

  function emptyCells(grid){ const res=[]; for(let y=0;y<grid.length;y++){ for(let x=0;x<grid[0].length;x++){ if(grid[y][x]===0) res.push([x,y]); } } return res; }

  function placeItems(grid, count, avoidSet, rng){
    const cells = emptyCells(grid).filter(([x,y])=>!avoidSet.has(x+","+y));
    shuffle(cells, rng);
    return cells.slice(0, count).map(([x,y])=>({x,y}));
  }

  function levelParams(level){
    return {
      size: sizeForLevel(level),
      loopAttempts: Math.floor(level*1.5),
      enemies: Math.min(1 + Math.floor(level/2), 10),
      traps: Math.min(3 + level, 80),
      powerups: Math.max(2, 5 - Math.floor(level/3))
    };
  }

  function generateLevel(level, seed){
    const rng = makeRNG(seed || (Date.now() ^ (level*9301)) >>> 0);
    const n = levelParams(level).size;
    const w=n, h=n;
    let grid = carveMaze(w,h,rng);
    addLoops(grid, levelParams(level).loopAttempts, rng);

    const start = {x:1, y:1};
    const exit = farthestFrom(grid, start.x, start.y);

    const avoid = new Set([start.x+","+start.y, exit.x+","+exit.y]);

    const enemies = placeItems(grid, levelParams(level).enemies, avoid, rng).map(p=>({x:p.x,y:p.y, cooldown:0}));
    const traps = placeItems(grid, levelParams(level).traps, avoid, rng).map(p=>({x:p.x,y:p.y, phase:(rng()*60)|0}));

    const powTypes = ['heal','shield','speed'];
    const powerups = placeItems(grid, levelParams(level).powerups, avoid, rng).map(p=>({x:p.x,y:p.y, kind: randChoice(powTypes, rng)}));

    return { grid, start, exit:{x:exit.x,y:exit.y}, enemies, traps, powerups, seedUsed: seed };
  }

  global.MazeGen = { generateLevel };
})(window);
