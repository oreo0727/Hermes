(function(){
  'use strict';
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');

  function fitCanvasToCSS(){
    const dpr = Math.max(1, window.devicePixelRatio||1);
    const cssW = Math.floor(canvas.clientWidth||720);
    const cssH = Math.floor(canvas.clientHeight||720);
    if(!cssW || !cssH) return; // wait for layout
    if(canvas.width !== cssW*dpr || canvas.height !== cssH*dpr){
      canvas.width = cssW*dpr; canvas.height = cssH*dpr;
      if(ctx.setTransform) ctx.setTransform(dpr,0,0,dpr,0,0);
    }
    if('imageSmoothingEnabled' in ctx) ctx.imageSmoothingEnabled = false;
    if('mozImageSmoothingEnabled' in ctx) ctx.mozImageSmoothingEnabled = false;
    if('webkitImageSmoothingEnabled' in ctx) ctx.webkitImageSmoothingEnabled = false;
  }
  window.addEventListener('resize', ()=> setTimeout(fitCanvasToCSS, 0));
  window.addEventListener('load', ()=> setTimeout(fitCanvasToCSS, 0));
  fitCanvasToCSS();

  const state = {
    tick:0,
    levelNum: 1,
    level: null,
    entities: [], // {type:'player'|'enemy'|'trap'|'power', x, y, ...}
    hearts: 3,
    cooldown: 0,
  };

  function hudUpdate(){
    const L = document.getElementById('hudLevel'); if(L) L.textContent = `Level ${state.levelNum}`;
    const H = document.getElementById('hudHearts'); if(H){ H.textContent = '❤'.repeat(Math.max(0,state.hearts)); }
  }

  function placeEntities(){
    const g = state.level.grid; const rows=g.length, cols=g[0].length;
    state.entities = [];
    // player at start
    state.entities.push({type:'player', x: state.level.start.x, y: state.level.start.y});
    // simple enemies
    const enemyCount = Math.min(1 + Math.floor(state.levelNum/2), 8);
    let placed = 0; let guard=0;
    while(placed<enemyCount && guard<5000){
      guard++;
      const x = (Math.random()*cols)|0, y=(Math.random()*rows)|0;
      if(g[y][x]===0){ const man = Math.abs(x-state.level.start.x)+Math.abs(y-state.level.start.y); if(man>=6){ state.entities.push({type:'enemy', x, y, cd:0}); placed++; } }
    }
    // traps
    const trapCount = Math.min(3 + state.levelNum, 60);
    for(let i=0;i<trapCount;i++){
      let tries=0; while(tries++<100){ const x=(Math.random()*cols)|0, y=(Math.random()*rows)|0; if(g[y][x]===0 && !(x===state.level.start.x&&y===state.level.start.y) && !(x===state.level.exit.x&&y===state.level.exit.y)){ state.entities.push({type:'trap', x,y, period: 60 + ((Math.random()*60)|0), phase: (Math.random()*60)|0}); break; } }
    }
    // powerups
    const powCount = Math.max(2, 5 - Math.floor(state.levelNum/3));
    for(let i=0;i<powCount;i++){
      let tries=0; while(tries++<100){ const x=(Math.random()*cols)|0, y=(Math.random()*rows)|0; if(g[y][x]===0 && !(x===state.level.start.x&&y===state.level.start.y) && !(x===state.level.exit.x&&y===state.level.exit.y)){ state.entities.push({type:'power', x,y}); break; } }
    }
  }

  function regen(){
    state.level = window.MazeGen.generateLevel(state.levelNum, Date.now());
    placeEntities(); hudUpdate();
  }

  function cellFree(x,y){ const g=state.level.grid; return g[y] && g[y][x]===0 && !state.entities.some(e=> e!==player && e.x===x && e.y===y && (e.type==='enemy')); }

  function findPlayer(){ return state.entities.find(e=> e.type==='player'); }
  const player = { get x(){ return findPlayer().x; }, get y(){ return findPlayer().y; }, set x(v){ findPlayer().x=v; }, set y(v){ findPlayer().y=v; } };

  function stepEnemies(){
    const g=state.level.grid; const rows=g.length, cols=g[0].length;
    for(let i=0;i<state.entities.length;i++){
      const e = state.entities[i]; if(e.type!=='enemy') continue;
      if(e.cd>0){ e.cd--; continue; }
      const dx = Math.sign(player.x - e.x), dy = Math.sign(player.y - e.y);
      let nx=e.x, ny=e.y;
      if(dx && g[e.y] && g[e.y][e.x+dx]===0) nx = e.x+dx; else if(dy && g[e.y+dy] && g[e.y+dy][e.x]===0) ny = e.y+dy; else {
        const opts=[[1,0],[-1,0],[0,1],[0,-1]]; for(let k=0;k<opts.length;k++){ const ox=opts[k][0], oy=opts[k][1]; if(g[e.y+oy] && g[e.y+oy][e.x+ox]===0){ nx=e.x+ox; ny=e.y+oy; break; } }
      }
      e.x=nx; e.y=ny; e.cd = Math.max(6, 10 - Math.min(6, state.levelNum));
    }
  }

  function tick(){
    state.tick++;
    if(state.cooldown>0) state.cooldown--;
    // player move
    if(state.cooldown===0){ const v = window.Input.sampleDir(); const nx = player.x + v[0], ny = player.y + v[1]; if((v[0]||v[1]) && cellFree(nx,ny)){ player.x=nx; player.y=ny; state.cooldown=8; } }
    // traps
    const onTrap = state.entities.find(e=> e.type==='trap' && e.x===player.x && e.y===player.y && ((state.tick + (e.phase||0)) % (e.period||60)) < ((e.period||60)/2) );
    if(onTrap){ state.hearts = Math.max(0, state.hearts-1); hudUpdate(); if(state.hearts===0){ state.levelNum=1; regen(); return; } }
    // powerups
    const pi = state.entities.findIndex(e=> e.type==='power' && e.x===player.x && e.y===player.y);
    if(pi>=0){ state.entities.splice(pi,1); state.hearts = Math.min(5, state.hearts+1); hudUpdate(); }
    // exit
    if(state.level.exit && player.x===state.level.exit.x && player.y===state.level.exit.y){ state.levelNum++; regen(); return; }
    // enemies
    stepEnemies();
  }

  function loop(){
    fitCanvasToCSS();
    tick();
    window.Renderer.render(state, ctx, canvas.width, canvas.height);
    requestAnimationFrame(loop);
  }

  regen(); hudUpdate();
  console.log('Game boot v1');
  requestAnimationFrame(loop);
})();
