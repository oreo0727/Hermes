(function(){
  const canvas = document.getElementById('game');
  const ctx = canvas.getContext('2d');
  const levelEl = document.getElementById('level');
  const healthEl = document.getElementById('health');
  const shieldEl = document.getElementById('shield');
  const msgEl = document.getElementById('msg');

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
    levelEl.textContent = `Level ${state.levelNum}`;
    const hearts = '❤'.repeat(state.player.hp) + '·'.repeat(Math.max(0,5-state.player.hp));
    healthEl.textContent = hearts;
    shieldEl.classList.toggle('hidden', !(state.player.shield>0));
  }

  const R = Math.random; // fallback RNG for non-critical parts

  const state = {
    levelNum: 1,
    level: null,
    player: {x:1,y:1,hp:3,shield:0,haste:0},
    ticks: 0,
    movingCooldown: 0,
    emit(type,text){ if(type==='msg'){ msgEl.textContent = text; setTimeout(()=>{ if(msgEl.textContent===text) msgEl.textContent=''; }, 1200); } }
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
    let [dx,dy]=[0,0];
    if(dir==='up') dy=-1; else if(dir==='down') dy=1; else if(dir==='left') dx=-1; else if(dir==='right') dx=1;
    const nx = state.player.x+dx, ny = state.player.y+dy;
    if(canMove(nx,ny)){
      state.player.x=nx; state.player.y=ny; state.movingCooldown = speed; beep(720,0.02,0.015);
    }
  }

  function gameOver(){
    beep(160,0.25,0.04);
    state.emit('msg','Fallen. Back to Level 1');
    state.player = {x:1,y:1,hp:3,shield:0,haste:0};
    startLevel(1);
  }

  function update(){
    state.ticks++;
    if(state.movingCooldown>0) state.movingCooldown--;
    if(state.player.haste>0) state.player.haste--;

    if(Input.consumePress('m')){ muted=!muted; }
    if(Input.consumePress('r')){ startLevel(state.levelNum); }

    // movement
    if(Input.keys.has('up')) tryMove('up');
    else if(Input.keys.has('down')) tryMove('down');
    else if(Input.keys.has('left')) tryMove('left');
    else if(Input.keys.has('right')) tryMove('right');

    // systems
    Enemies.updateEnemies(state, R);
    Traps.checkTrapDamage(state);
    Powerups.tryPickup(state);

    // collide with enemy
    for(const e of state.level.enemies){ if(e.x===state.player.x && e.y===state.player.y){
      if(state.player.shield>0){ state.player.shield=0; state.emit('msg','Shield broke!'); }
      else { state.player.hp=Math.max(0,state.player.hp-1); state.emit('msg','Bitten!'); }
      beep(320,0.06,0.03);
    }}

    // win check
    if(state.player.x===state.level.exit.x && state.player.y===state.level.exit.y){
      beep(880,0.12,0.03); setTimeout(()=>beep(980,0.12,0.03),60);
      state.emit('msg','Safe clearing!');
      startLevel(state.levelNum+1);
    }

    if(state.player.hp<=0) gameOver();

    setHUD(state);
  }

  function draw(){ Renderer.render(state, ctx, canvas.width, canvas.height); }

  function loop(){ update(); draw(); requestAnimationFrame(loop); }

  function fitCanvasToCSS(){
    const dpr = Math.max(1, window.devicePixelRatio||1);
    const cssW = Math.floor(canvas.clientWidth||720);
    const cssH = Math.floor(canvas.clientHeight||720);
    if(!cssW || !cssH) return; // try again on next tick
    canvas.width = Math.max(1, cssW * dpr);
    canvas.height = Math.max(1, cssH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.imageSmoothingEnabled = false;
  }

  window.addEventListener('resize', ()=>{ setTimeout(fitCanvasToCSS, 0); });
  window.addEventListener('load', ()=>{
    setTimeout(fitCanvasToCSS, 0);
    // Prefer a user-provided grid pack if present, then fall back to JSON atlas.
    (async function init(){
      // Prefer JSON atlas first (precise mapping), then fallback to user grid pack if present
      let atlasOk = false;
      if (window.loadAtlas){
        const base='assets/sheets/spritesheet.json';
        const url = (window.pickAtlasUrl? window.pickAtlasUrl(base) : base);
        try {
          await loadAtlas(url);
          atlasOk = !!window.SPRITES_READY;
          if(atlasOk) console.log('Atlas installed:', url);
        } catch(e){
          console.warn('Atlas load failed for', url, e);
          if(url!==base){
            try { await loadAtlas(base); atlasOk=!!window.SPRITES_READY; if(atlasOk) console.log('Base atlas installed:', base); }
            catch(e2){ console.warn('Base atlas also failed:', e2); }
          }
        }
      }
      if (!atlasOk && window.tryInstallDefaultUserPack){
        try {
          const ok = await window.tryInstallDefaultUserPack();
          if(ok) console.log('User grid pack installed (fallback)');
        } catch(e){ console.warn('User grid pack probe failed:', e); }
      }
      startLevel(1); loop();
    })();
  });
})();
