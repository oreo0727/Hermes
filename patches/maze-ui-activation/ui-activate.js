(function(){
  // Idempotent installer: safe to run multiple times
  const d = document;
  function ensure(el, parent, styles){ if(!el.isConnected) parent.appendChild(el); if(styles) Object.assign(el.style, styles); return el; }

  function installBadge(){
    const badgeId = 'uiActiveBadge';
    let b = d.getElementById(badgeId);
    if(!b){ b = d.createElement('div'); b.id = badgeId; b.textContent = 'UI ACTIVE'; }
    ensure(b, d.body, {
      position:'fixed', top:'8px', left:'8px', zIndex: 100000,
      background:'#2b8a3e', color:'#fff', padding:'4px 8px', borderRadius:'12px',
      font:'12px/1.2 system-ui, sans-serif', pointerEvents:'none', opacity:'0.92',
      boxShadow:'0 2px 8px rgba(0,0,0,.25)'
    });
  }

  function installLayering(){
    const root = d.getElementById('gameRoot') || d.body;
    const canvas = d.getElementById('game') || d.querySelector('canvas');
    if(root && root !== d.body){ root.style.position = root.style.position || 'relative'; }
    if(canvas){
      canvas.style.display = canvas.style.display || 'block';
      canvas.style.position = canvas.style.position || 'relative';
      canvas.style.zIndex = canvas.style.zIndex || '10';
      // Keep a crisp square if CSS allows
      canvas.style.width = canvas.style.width || '100%';
      if(!canvas.style.aspectRatio) canvas.style.aspectRatio = '1';
    }
    // HUD rules: non-blocking by default, above canvas
    let hud = d.getElementById('hudTL');
    if(!hud){ hud = d.createElement('div'); hud.id='hudTL'; hud.setAttribute('aria-hidden','false'); hud.textContent='HUD'; (root||d.body).appendChild(hud); }
    Object.assign(hud.style, {
      position: hud.style.position || 'absolute',
      top: hud.style.top || '12px', left: hud.style.left || '12px',
      zIndex: parseInt(hud.style.zIndex||'20',10),
      pointerEvents: hud.style.pointerEvents || 'none',
      color: hud.style.color || '#fff',
      textShadow: hud.style.textShadow || '0 1px 2px rgba(0,0,0,.7)'
    });
    // Re-enable pointer events for interactive controls inside HUD
    hud.querySelectorAll('button,a,[role="button"],input,select,textarea').forEach(el=>{
      el.style.pointerEvents = 'auto';
    });

    // Demote any generic overlays that might occlude the canvas
    d.querySelectorAll('.overlay,.vignette,.frame,[data-role="overlay"]').forEach(el=>{
      el.style.zIndex = '1'; el.style.pointerEvents='none';
    });
  }

  function fitCanvasToCSS(){
    const c = d.getElementById('game'); if(!c) return;
    const ctx = c.getContext && c.getContext('2d'); if(!ctx) return;
    const dpr = Math.max(1, window.devicePixelRatio||1);
    const cssW = Math.floor(c.clientWidth||0);
    const cssH = Math.floor(c.clientHeight||0);
    if(!cssW || !cssH) return; // try again later
    if(c.width !== cssW*dpr || c.height !== cssH*dpr){
      c.width = cssW*dpr; c.height = cssH*dpr;
      if(ctx.setTransform) ctx.setTransform(dpr,0,0,dpr,0,0);
    }
  }

  function installToggles(){
    const HELP_ID = 'uiHelpPanel';
    let panel = d.getElementById(HELP_ID);
    if(!panel){
      panel = d.createElement('div'); panel.id = HELP_ID; panel.className = 'hidden';
      panel.innerHTML = '<div style="font:12px/1.4 system-ui,sans-serif; color:#fff">'+
        '<strong>HUD Help</strong><br/>H: toggle HUD, f: help, Esc: close overlays'+
        '</div>';
      Object.assign(panel.style, {
        position:'fixed', top:'8px', right:'8px', zIndex: 100001,
        background:'rgba(0,0,0,.75)', padding:'8px 10px', borderRadius:'8px',
        display:'none', maxWidth:'45vw'
      });
      d.body.appendChild(panel);
    }
    function show(b){ panel.style.display = b ? 'block' : 'none'; panel.classList.toggle('hidden', !b); }
    let hudVisible = true, helpVisible = false;
    function setHudVisible(v){
      const hud = d.getElementById('hudTL'); if(!hud) return; hud.style.display = v ? '' : 'none'; hudVisible = v;
    }
    function onKey(e){
      if(e.key === 'H' || e.key === 'h'){ setHudVisible(!hudVisible); }
      else if(e.key === '?' || (e.shiftKey && e.key==='/')){ helpVisible = !helpVisible; show(helpVisible); }
      else if(e.key === 'Escape'){ if(helpVisible){ helpVisible = false; show(false); } }
    }
    d.addEventListener('keydown', onKey);
  }

  function install(){
    try{ console.log('[UI-Activate] Installing Maze UI activation kit'); }catch(_){ }
    installBadge();
    installLayering();
    fitCanvasToCSS();
    window.addEventListener('resize', ()=> setTimeout(fitCanvasToCSS,0));
    window.addEventListener('load', ()=> setTimeout(fitCanvasToCSS,0));
    installToggles();
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', install);
  } else {
    install();
  }
})();