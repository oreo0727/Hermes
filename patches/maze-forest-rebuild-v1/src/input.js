(function(){
  'use strict';
  const keys = new Set();
  let lastAxis = 'x';
  window.addEventListener('keydown', e=>{
    const k=e.key; if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].includes(k)) e.preventDefault();
    if(e.repeat) return; keys.add(k);
    if(k==='ArrowLeft'||k==='ArrowRight'||k==='a'||k==='d') lastAxis='x';
    if(k==='ArrowUp'||k==='ArrowDown'||k==='w'||k==='s') lastAxis='y';
  });
  window.addEventListener('keyup', e=>{ keys.delete(e.key); });

  function sampleDir(){
    // prevent diagonals; use lastAxis preference
    const left = keys.has('ArrowLeft')||keys.has('a');
    const right= keys.has('ArrowRight')||keys.has('d');
    const up   = keys.has('ArrowUp')||keys.has('w');
    const down = keys.has('ArrowDown')||keys.has('s');
    const dx = (left? -1 : 0) + (right? 1:0);
    const dy = (up? -1 : 0) + (down? 1:0);
    if(dx && dy){ return lastAxis==='x' ? [dx,0] : [0,dy]; }
    if(dx) return [dx,0]; if(dy) return [0,dy]; return [0,0];
  }

  window.Input = { sampleDir };
})();
