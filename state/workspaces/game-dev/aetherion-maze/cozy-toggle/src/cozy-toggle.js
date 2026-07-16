(function(){
  // Cozy Mode UI Toggle
  // Depends on flags.js initializing window.MF_COZY_MODE and window.MF_VERSION (optional)
  function $(sel){ return document.querySelector(sel); }
  function update(btn){
    const on = !!window.MF_COZY_MODE;
    if(!btn) return;
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    btn.textContent = on ? 'Cozy: On' : 'Cozy: Off';
    btn.classList.toggle('off', !on);
    btn.title = 'Toggle Cozy visuals (default ON). Currently: ' + (on ? 'On' : 'Off');
  }
  function setCozy(on){
    try{ localStorage.setItem('MF_COZY', on ? '1' : '0'); }catch(_){ }
    window.MF_COZY_MODE = !!on;
    const ev = new CustomEvent('mf:cozy-changed', { detail: { cozy: !!on } });
    window.dispatchEvent(ev);
  }
  function init(){
    const root = document.getElementById('hudTR') || (function(){
      const d = document.createElement('div');
      d.id = 'hudTR'; d.className = 'ui-controls';
      d.setAttribute('role','region'); d.setAttribute('aria-label','Display options');
      const parent = document.getElementById('gameRoot') || document.body; parent.appendChild(d);
      return d;
    })();
    let btn = document.getElementById('btnCozy');
    if(!btn){
      btn = document.createElement('button');
      btn.id = 'btnCozy'; btn.type = 'button';
      root.appendChild(btn);
    }
    btn.addEventListener('click', function(){ setCozy(!window.MF_COZY_MODE); update(btn); });
    update(btn);
    // Keep in sync if changed elsewhere (e.g., dev console/localStorage)
    window.addEventListener('storage', function(e){ if(e && e.key==='MF_COZY'){ window.MF_COZY_MODE = (e.newValue==='1' || e.newValue==='true'); update(btn); } });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
