(function(){
  const state = { keys: new Set(), lastAxis: null };
  function onDown(e){
    // Prevent page scroll on navigation keys
    if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' ','Space','PageUp','PageDown'].includes(e.key)){
      try{ e.preventDefault(); }catch(_){ }
    }
    // Ignore OS key repeats to avoid flooding
    if(e.repeat) return;

    const k = e.key;
    if(['ArrowUp','w','W'].includes(k)) { state.lastAxis='y'; state.keys.add('up'); }
    else if(['ArrowDown','s','S'].includes(k)) { state.lastAxis='y'; state.keys.add('down'); }
    else if(['ArrowLeft','a','A'].includes(k)) { state.lastAxis='x'; state.keys.add('left'); }
    else if(['ArrowRight','d','D'].includes(k)) { state.lastAxis='x'; state.keys.add('right'); }
  }
  function onUp(e){
    const k = e.key;
    if(['ArrowUp','w','W'].includes(k)) state.keys.delete('up');
    else if(['ArrowDown','s','S'].includes(k)) state.keys.delete('down');
    else if(['ArrowLeft','a','A'].includes(k)) state.keys.delete('left');
    else if(['ArrowRight','d','D'].includes(k)) state.keys.delete('right');
  }

  function direction(){
    // no diagonals; prefer lastAxis
    const x = (state.keys.has('left')?-1:0) + (state.keys.has('right')?1:0);
    const y = (state.keys.has('up')?-1:0) + (state.keys.has('down')?1:0);
    if(x && y){
      if(state.lastAxis==='x') return [Math.sign(x),0];
      if(state.lastAxis==='y') return [0,Math.sign(y)];
      // default to y
      return [0,Math.sign(y)];
    }
    if(x) return [Math.sign(x),0];
    if(y) return [0,Math.sign(y)];
    return [0,0];
  }

  function attach(){
    window.addEventListener('keydown', onDown, { passive:false });
    window.addEventListener('keyup', onUp, { passive:true });
  }
  function detach(){
    window.removeEventListener('keydown', onDown);
    window.removeEventListener('keyup', onUp);
  }

  window.Input = { attach, detach, direction };
})();
