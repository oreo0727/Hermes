(function(){
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  const coinsEl = document.getElementById('coins');
  const keysEl = document.getElementById('keys');

  let muted=false;
  function beep(freq=640, dur=0.05, vol=0.02){
    if(muted) return;
    try{
      const ac = beep.ac || (beep.ac = new (window.AudioContext||window.webkitAudioContext)());
      const o = ac.createOscillator(); const g = ac.createGain(); o.connect(g); g.connect(ac.destination);
      o.type='sine'; o.frequency.value=freq; g.gain.value=vol; o.start(); o.stop(ac.currentTime+dur);
    }catch(_){/*no audio*/}
  }

  function setHUD(state){
    if(coinsEl){ coinsEl.textContent = state.level ? Math.max(0, state.level.powerups.length) : 0; }
    if(keysEl){ keysEl.textContent = '0/0'; }
  }

  const R = Math.random; // fallback RNG for non-critical parts

  const state = {
    levelNum: 1,
    level: null,
    player: {x:1,y:1,hp:3,shield:0,haste:0},
    ticks: 0,
    movingCooldown: 0,
    emit(type,text){ /* minimal msg bus; can extend */ }
  };

  function startLevel(n){
    state.levelNum = n;
    state.level = MazeGen.generateLevel(n);
    state.player.x = state.level.start.x;
    state.player.y = state.level.start.y;
    state.movingCooldown = 0;
    if(n>1){ state.player.hp = Math.min(5, state.player.hp+1); }
    beep(520,0.08,0.03);
    setHUD(state);
  }

  function canMove(nx,ny){ const g=state.level.grid; return g[ny] && g[ny][nx]===0; }

  function tryMove(dir){
    const speed = state.player.haste>0 ? 2 : 4; // lower is faster (cooldown frames)
    if(state.movingCooldown>0) return;
    let dx=0, dy=0;
    if(dir==='up') dy=-1; else if(dir==='down') dy=1; else if(dir==='left') dx=-1; else if(dir==='right') dx=1;
    const nx = state.player.x+dx, ny = state.player.y+dy;
    if(canMove(nx,ny)){
      state.player.x=nx; state.player.y=ny; state.movingCooldown = speed; beep(720,0.02,0.015);
    }
  }

  function gameOver(){
    beep(160,0.25,0.04);
    state.player = {x:1,y:1,hp:3,shield:0,haste:0};
    startLevel(1);
  }

  function update(){
    state.ticks++;
    if(state.movingCooldown>0) state.movingCooldown--;
    if(state.player.haste>0) state.player.haste--;

    if(Input.consumePress && Input.consumePress('m')){ muted=!muted; }
    if(Input.consumePress && Input.consumePress('r')){ startLevel(state.levelNum); }

    // movement
    if(Input.keys && Input.keys.has('up')) tryMove('up');
    else if(Input.keys && Input.keys.has('down')) tryMove('down');
    else if(Input.keys && Input.keys.has('left')) tryMove('left');
    else if(Input.keys && Input.keys.has('right')) tryMove('right');

    // systems
    if(typeof Enemies!=='undefined' && Enemies.updateEnemies) Enemies.updateEnemies(state, R);
    if(typeof Traps!=='undefined' && Traps.checkTrapDamage) Traps.checkTrapDamage(state);
    if(typeof Powerups!=='undefined' && Powerups.tryPickup) Powerups.tryPickup(state);

    // collide with enemy
    if(state.level && Array.isArray(state.level.enemies)){
      for(let i=0;i<state.level.enemies.length;i++){
        const e=state.level.enemies[i];
        if(e.x===state.player.x && e.y===state.player.y){
          if(state.player.shield>0){ state.player.shield=0; }
          else { state.player.hp=Math.max(0,state.player.hp-1); }
          beep(320,0.06,0.03);
        }
      }
    }

    // win check
    if(state.player.x===state.level.exit.x && state.player.y===state.level.exit.y){
      beep(880,0.12,0.03); setTimeout(()=>beep(980,0.12,0.03),60);
      startLevel(state.levelNum+1);
    }

    if(state.player.hp<=0) gameOver();

    setHUD(state);
  }

  function draw(){
    const W = canvas.clientWidth|0; const H = canvas.clientHeight|0;
    Renderer.render(state, ctx, W, H);
  }

  function fitCanvasToCSS(){
    const dpr = Math.max(1, window.devicePixelRatio||1);
    const cssW = Math.floor(canvas.clientWidth||720);
    const cssH = Math.floor(canvas.clientHeight||720);
    if(!cssW || !cssH) return; // not laid out yet
    if(canvas.width !== cssW*dpr || canvas.height !== cssH*dpr){
      canvas.width = cssW*dpr; canvas.height = cssH*dpr;
      if (ctx && ctx.setTransform) ctx.setTransform(dpr,0,0,dpr,0,0);
      ctx.imageSmoothingEnabled = false;
    }
  }

  function layout(){
    // CSS enforces aspect ratio on canvas; just ensure DPR fit.
    fitCanvasToCSS();
  }

  function loop(){ update(); draw(); requestAnimationFrame(loop); }

  window.addEventListener('resize', ()=> setTimeout(layout, 0));
  window.addEventListener('load', ()=>{ setTimeout(layout,0); startLevel(1); loop(); });
})();
