// Guarded addLoops replacement for Maze Forest generator
// - Never throws if grid shape/values are unexpected
// - Only opens a single wall cell between two floor cells two steps apart
// - density is the approximate fraction of cells considered for loop creation
// Usage: integrate into your generator.js, replacing the old addLoops

(function(global){
  function inBounds(x, y, rows, cols){
    return y >= 0 && y < rows && x >= 0 && x < cols;
  }

  // Attempt to infer which value represents floor vs wall.
  // Heuristic: treat the most common value among a central sample as FLOOR if its 0/falsey; otherwise assume 0=floor, 1=wall fallback.
  function inferValues(grid, rows, cols){
    try {
      const sample = [];
      const y0 = Math.max(0, Math.floor(rows*0.25));
      const y1 = Math.min(rows, Math.ceil(rows*0.75));
      const x0 = Math.max(0, Math.floor(cols*0.25));
      const x1 = Math.min(cols, Math.ceil(cols*0.75));
      const counts = new Map();
      for (let y=y0; y<y1; y++){
        const row = grid[y]; if (!row) break;
        for (let x=x0; x<x1; x++){
          const v = row[x];
          counts.set(v, (counts.get(v)||0)+1);
        }
      }
      let modeVal = 0, modeCount = -1;
      for (const [k,c] of counts){ if (c>modeCount){ modeCount=c; modeVal=k; } }
      // If mode is 0 or falsey, prefer 0 as FLOOR.
      const floorVal = (modeVal===0 || modeVal===false) ? 0 : 0;
      const wallVal = floorVal===0 ? 1 : 1; // conservative fallback
      return { floorVal, wallVal };
    } catch(e){
      return { floorVal: 0, wallVal: 1 };
    }
  }

  function addLoopsSafe(grid, rows, cols, density){
    try{
      if (!Array.isArray(grid) || !rows || !cols) return; // nothing to do
      const { floorVal, wallVal } = inferValues(grid, rows, cols);
      const DIRS = [ [1,0], [-1,0], [0,1], [0,-1] ];
      const total = Math.max(1, Math.floor((rows*cols) * (typeof density === 'number' ? density : 0.05)));
      let added = 0;
      let attempts = 0;
      const maxAttempts = total * 20; // generous guard

      while (added < total && attempts++ < maxAttempts){
        const x = 1 + Math.floor(Math.random() * Math.max(1, cols-2));
        const y = 1 + Math.floor(Math.random() * Math.max(1, rows-2));
        const cellRow = grid[y];
        if (!cellRow) continue;
        if (cellRow[x] !== floorVal) continue; // only operate from a carved cell

        const [dx, dy] = DIRS[Math.floor(Math.random()*DIRS.length)];
        const mx = x + dx;      // mid wall
        const my = y + dy;
        const nx = x + dx*2;    // opposite cell
        const ny = y + dy*2;
        if (!inBounds(nx, ny, rows, cols)) continue;

        const midRow = grid[my];
        const nextRow = grid[ny];
        if (!midRow || !nextRow) continue;

        const mid = midRow[mx];
        const next = nextRow[nx];

        // Only carve if mid is a wall and next is a floor (connect two passages)
        if (mid === wallVal && next === floorVal){
          midRow[mx] = floorVal;
          added++;
        }
      }
      // Return added count for diagnostics if needed
      return added;
    } catch (e){
      // Safety: never throw from addLoops
      if (typeof console !== 'undefined' && console.warn){
        console.warn('[addLoopsSafe] suppressed error:', e && e.message ? e.message : e);
      }
      return 0;
    }
  }

  // Attach in a few common places
  global.addLoopsSafe = addLoopsSafe;
  if (global.MazeGen && typeof global.MazeGen === 'object'){
    global.MazeGen.addLoops = addLoopsSafe;
  }

})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
