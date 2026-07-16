(function(){
  function neighbors2(r,c){ return [[r-2,c],[r+2,c],[r,c-2],[r,c+2]]; }
  function neighbors4(r,c){ return [[r-1,c],[r+1,c],[r,c-1],[r,c+1]]; }
  function inb(grid, r, c){ return r>=0 && c>=0 && r<grid.length && c<grid[0].length; }

  function makeGrid(rows, cols){ const g=[]; for(let r=0;r<rows;r++){ const row=[]; for(let c=0;c<cols;c++){ row.push(0); } g.push(row);} return g; }

  function carveBacktracker(rows, cols){
    const grid = makeGrid(rows, cols);
    // initialize: walls (0) everywhere, floors will be 1
    const stack=[];
    const start = [1,1];
    grid[start[0]][start[1]] = 1;
    stack.push(start);
    while(stack.length){
      const [cr, cc] = stack[stack.length-1];
      const options = neighbors2(cr,cc).filter(([nr,nc])=> inb(grid,nr,nc) && grid[nr][nc]===0);
      if(options.length){
        const [nr,nc] = options[(Math.random()*options.length)|0];
        // carve wall between
        const wr = cr + Math.sign(nr-cr);
        const wc = cc + Math.sign(nc-cc);
        grid[wr][wc] = 1;
        grid[nr][nc] = 1;
        stack.push([nr,nc]);
      } else {
        stack.pop();
      }
    }
    return {grid, start};
  }

  function bfs(grid, sr, sc){
    const R=grid.length, C=grid[0].length;
    const dist = Array.from({length:R},()=>Array(C).fill(Infinity));
    const prev = Array.from({length:R},()=>Array(C).fill(null));
    const q=[[sr,sc]]; dist[sr][sc]=0; let qi=0;
    while(qi<q.length){
      const cur = q[qi++]; const r=cur[0], c=cur[1];
      const nbs = neighbors4(r,c);
      for(let i=0;i<nbs.length;i++){
        const nr = nbs[i][0], nc = nbs[i][1];
        if(inb(grid,nr,nc) && grid[nr][nc]===1 && dist[nr][nc]===Infinity){
          dist[nr][nc]=dist[r][c]+1; prev[nr][nc]=[r,c]; q.push([nr,nc]);
        }
      }
    }
    return {dist, prev};
  }

  function farthestExit(grid, sr, sc){
    const {dist} = bfs(grid, sr, sc);
    let best=[sr,sc], bestd=-1;
    for(let r=1;r<grid.length;r+=2){
      for(let c=1;c<grid[0].length;c+=2){
        if(grid[r][c]===1 && dist[r][c]!==Infinity && dist[r][c]>bestd){ bestd=dist[r][c]; best=[r,c]; }
      }
    }
    return {er: best[0], ec: best[1], distance: bestd, dist};
  }

  function reconstructPath(prev, er, ec){
    const path=[]; let cur=[er,ec];
    while(cur){ path.push(cur); cur = prev[cur[0]][cur[1]]; }
    return path.reverse();
  }

  function addLoops(grid, attempts){
    const R=grid.length, C=grid[0].length;
    let added=0; let tries=0;
    while(added<attempts && tries<attempts*20){
      tries++;
      const r = (2+((Math.random()*(R-3))|0))|0; // avoid borders a bit
      const c = (2+((Math.random()*(C-3))|0))|0;
      if(grid[r][c]!==0) continue; // pick a wall
      let adjFloors=0; const nbs = neighbors4(r,c); for(let i=0;i<nbs.length;i++){ const nr=nbs[i][0], nc=nbs[i][1]; if(inb(grid,nr,nc) && grid[nr][nc]===1) adjFloors++; }
      if(adjFloors>=2){ grid[r][c]=1; added++; }
    }
    return added;
  }

  function ensureOdd(n){ return (n%2===0)? n+1 : n; }

  function sizeForLevel(level){ const base=15; const inc = Math.min( (level-1)*2, 36 ); return ensureOdd(base+inc); }

  function generateLevel(level){
    const rows = sizeForLevel(level), cols = sizeForLevel(level);
    const {grid, start} = carveBacktracker(rows, cols);
    addLoops(grid, Math.floor(level*1.5));
    const fr = start[0], fc = start[1];
    const {er, ec} = farthestExit(grid, fr, fc);
    const {prev} = bfs(grid, fr, fc);
    const path = reconstructPath(prev, er, ec);
    // Mark exit as 2 for renderer
    grid[er][ec] = 2;
    return { grid, start: {r:fr, c:fc}, exit: {r:er, c:ec}, path };
  }

  window.Generator = { generateLevel, sizeForLevel };
})();
