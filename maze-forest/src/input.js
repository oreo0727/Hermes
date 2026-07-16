(function(global){
  const keys = new Set();
  const pressed = new Set();

  function key(e,down){
    const k = e.key.toLowerCase();
    if(['arrowup','w'].includes(k)) { down? keys.add('up') : keys.delete('up'); pressed.add('up'); }
    if(['arrowdown','s'].includes(k)) { down? keys.add('down') : keys.delete('down'); pressed.add('down'); }
    if(['arrowleft','a'].includes(k)) { down? keys.add('left') : keys.delete('left'); pressed.add('left'); }
    if(['arrowright','d'].includes(k)) { down? keys.add('right') : keys.delete('right'); pressed.add('right'); }
    if(k==='r') { pressed.add('r'); }
    if(k==='m') { pressed.add('m'); }
  }

  window.addEventListener('keydown', e=>key(e,true));
  window.addEventListener('keyup', e=>key(e,false));

  function consumePress(k){ const had = pressed.has(k); pressed.delete(k); return had; }

  global.Input = { keys, consumePress };
})(window);
