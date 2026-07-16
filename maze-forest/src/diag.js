(function(){
  // Enable via ?debug=1 or localStorage.mf_debug='1'
  function isDebug(){
    try{ if(new URLSearchParams(location.search).get('debug')==='1') return true; }catch(_){ }
    try{ return localStorage.getItem('mf_debug')==='1'; }catch(_){ return false; }
  }
  if(!isDebug()) return;

  const badge = document.createElement('div');
  badge.textContent = 'Renderer probe';
  Object.assign(badge.style, {
    position:'fixed', top:'8px', left:'8px', zIndex: 99999,
    background:'#a12aff', color:'#fff', padding:'4px 8px', borderRadius:'12px',
    font:'12px/1.2 system-ui, sans-serif', pointerEvents:'none', opacity:'0.9'
  });
  document.addEventListener('DOMContentLoaded', ()=>document.body.appendChild(badge));

  const box = document.createElement('pre');
  Object.assign(box.style, {
    position:'fixed', top:'8px', right:'8px', zIndex: 99999,
    background:'rgba(0,0,0,0.8)', color:'#fff', padding:'8px',
    font:'11px/1.3 ui-monospace, SFMono-Regular, Menlo, monospace',
    maxWidth:'45vw', maxHeight:'40vh', overflow:'auto', margin:0
  });
  const log = (label, e)=>{ const ts=new Date().toISOString(); const msg = e && e.stack || String(e); box.textContent = `${ts}\n${label}: ${msg}`; if(!box.isConnected) document.body.appendChild(box); console.error(ts, label, e); };
  window.addEventListener('error', e=> log('Error', e.error||e.message||e));
  window.addEventListener('unhandledrejection', e=> log('Unhandled', e.reason||e));
})();
