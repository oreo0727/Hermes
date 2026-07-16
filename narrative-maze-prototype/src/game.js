(function(){
  const state = {
    levelNum: 1,
    level: null,
    player: null,
    flags: {},
    canMove: true,
    storyOpen: false,
  };

  const MOVE_COOLDOWN_MS = 120; // ~8 moves/sec; adjust for feel
  let lastMoveAt = 0;

  let ctx, canvas, raf;


  function tileAt(r,c){
    const g = state.level && state.level.grid; if(!g) return 0; return g[r] && g[r][c]!=null ? g[r][c] : 0;
  }

  function canStep(r,c){ return tileAt(r,c) !== 0; }

  let lastFocusedBeforeOverlay = null;

  function tabbables(root){
    return Array.from(root.querySelectorAll('[tabindex]:not([tabindex="-1"]), button, [href], input, select, textarea'))
      .filter(el => !el.hasAttribute('disabled') && el.offsetParent !== null);
  }

  function openStoryFor(node){
    const data = window.Narrative.getStoryById(node.storyId);
    if(!data) return;
    try{ console.debug('Open story', node.storyId); }catch(_){ }
    state.storyOpen = true; state.canMove = false;
    const overlay = document.getElementById('storyOverlay');
    const box = document.getElementById('storyBox');
    const textEl = document.getElementById('storyText');
    const choicesEl = document.getElementById('storyChoices');
    const contBtn = document.getElementById('storyContinue');
    overlay.classList.remove('hidden');
    overlay.setAttribute('aria-hidden','false');
    textEl.textContent = data.text;
    contBtn.classList.add('hidden');
    choicesEl.innerHTML = '';
    if(data.choices && data.choices.length){
      for(const ch of data.choices){
        const b = document.createElement('button'); b.textContent = ch.label; b.addEventListener('click', ()=>{
          try{ ch.effect && ch.effect(state.flags); }catch(_){ }
          closeStory();
        });
        choicesEl.appendChild(b);
      }
    } else {
      contBtn.classList.remove('hidden');
      contBtn.onclick = ()=> closeStory();
    }

    // Focus trap and focus restore setup
    lastFocusedBeforeOverlay = document.activeElement;
    try{ overlay.focus(); }catch(_){ }
    const els = tabbables(overlay);
    const first = els[0] || contBtn; const last = els[els.length-1] || contBtn;
    const trap = (e)=>{
      if(e.key==='Tab'){
        if(els.length===0){ e.preventDefault(); try{ overlay.focus(); }catch(_){ } return; }
        if(e.shiftKey && document.activeElement===first){ e.preventDefault(); last.focus(); }
        else if(!e.shiftKey && document.activeElement===last){ e.preventDefault(); first.focus(); }
      } else if(e.key==='Escape'){
        closeStory();
      }
    };
    overlay._trap = trap;
    overlay.addEventListener('keydown', trap);
  }

  function closeStory(){
    const overlay = document.getElementById('storyOverlay');
    overlay.classList.add('hidden');
    overlay.setAttribute('aria-hidden','true');
    if(overlay._trap){ overlay.removeEventListener('keydown', overlay._trap); delete overlay._trap; }
    if(lastFocusedBeforeOverlay && document.body.contains(lastFocusedBeforeOverlay)){
      try{ lastFocusedBeforeOverlay.focus(); }catch(_){ }
    }
    state.storyOpen = false; state.canMove = true;
  }

  function removeStoryNodeAt(r,c){
    if(!state.level || !state.level.storyNodes) return;
    const i = state.level.storyNodes.findIndex(n=> n.r===r && n.c===c);
    if(i>=0) state.level.storyNodes.splice(i,1);
  }

  function update(){
    if(!state.level || !state.player) return;
    if(state.canMove && !state.storyOpen){
      const now = (typeof performance !== 'undefined' && performance.now) ? performance.now() : Date.now();
      const [dx,dy] = window.Input.direction();
      if(dx||dy){
        if(now - lastMoveAt >= MOVE_COOLDOWN_MS){
          const nr = state.player.r + dy; const nc = state.player.c + dx;
          if(canStep(nr,nc)){
            state.player.r = nr; state.player.c = nc;
            lastMoveAt = now;
            // story interaction
            const node = state.level.storyNodes && state.level.storyNodes.find(n=> n.r===nr && n.c===nc);
            if(node){ openStoryFor(node); removeStoryNodeAt(nr,nc); }
            // exit
            if(tileAt(nr,nc)===2){
              nextLevel();
              return; // regeneration will change level
            }
          }
        }
      }
    }
  }

  function loop(){
    update();
    if(ctx){ window.Renderer.render(ctx, state); }
    raf = requestAnimationFrame(loop);
  }

  function nextLevel(){
    state.levelNum += 1;
    buildLevel();
  }

  function reset(){
    state.levelNum = 1; state.flags = {}; buildLevel();
  }

  function buildLevel(){
    const L = window.Generator.generateLevel(state.levelNum);
    // place stories along main path
    const storyNodes = window.Narrative.placeStoryNodes(L.path, L.grid);
    state.level = { grid: L.grid, start: L.start, exit: L.exit, path: L.path, storyNodes };
    state.player = { r: L.start.r, c: L.start.c };
    const lvEl = document.getElementById('level'); if(lvEl) lvEl.textContent = String(state.levelNum);
  }

  function start(c){
    canvas = c; ctx = c.getContext('2d');
    window.Input.attach();
    // keyboard QoL
    window.addEventListener('keydown', (e)=>{
      if(e.key==='r' || e.key==='R'){ reset(); }
    });
    // handle resize to keep canvas crisp
    const onResize = ()=>{
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.floor(rect.width * dpr);
      canvas.height = Math.floor(rect.height * dpr);
    };
    window.addEventListener('resize', onResize); onResize();

    buildLevel();
    cancelAnimationFrame(raf); raf = requestAnimationFrame(loop);
  }

  window.Game = { start, reset };
})();
