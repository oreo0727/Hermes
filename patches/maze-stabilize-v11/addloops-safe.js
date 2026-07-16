// addloops-safe.js
// Drop-in, bounds-checked replacement for brittle addLoops implementations.
// Guarantees: never throws; returns how many walls were opened. Works with 0/1 grid semantics.

(function(global){
  // Fallback cardinal directions if none provided by the generator.
  var DIRS = (global.DIRS && Array.isArray(global.DIRS)) ? global.DIRS : [
    [1,0],[-1,0],[0,1],[0,-1]
  ];

  function isArray2D(g){ return Array.isArray(g) && g.length>0 && Array.isArray(g[0]); }

  function addLoopsSafe(grid, loops, rng){
    if(!isArray2D(grid)) return 0;
    var h = grid.length, w = grid[0].length;
    if(!w || !h) return 0;
    // detect wall/floor semantics by sampling center-ish cell
    function isWall(x,y){ return y>=0 && y<h && x>=0 && x<w && grid[y] && grid[y][x]===1; }
    function isFloor(x,y){ return y>=0 && y<h && x>=0 && x<w && grid[y] && grid[y][x]===0; }
    var added=0, attempts=0, maxAttempts=Math.max((loops|0)*40, 200);
    var R = (typeof rng==='function') ? rng : Math.random;

    while(added < (loops|0) && attempts < maxAttempts){
      attempts++;
      var x = 1 + ((R()*(w-2))|0);
      var y = 1 + ((R()*(h-2))|0);
      if(!isWall(x,y)) continue;
      // Count neighboring floors; if at least 2, open this wall.
      var floors=0;
      for(var i=0;i<4;i++){
        var d = DIRS[i] || [0,0];
        var nx = x + (d[0]|0), ny = y + (d[1]|0);
        if(isFloor(nx,ny)) floors++;
      }
      if(floors>=2){ grid[y][x]=0; added++; }
    }
    return added;
  }

  // Expose for monkey-patch and direct import
  global.addLoopsSafe = addLoopsSafe;
})(typeof window!=='undefined'?window:globalThis);
