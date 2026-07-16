(function(global){
  function tryPickup(state){
    const p = state.player; const list = state.level.powerups;
    for(let i=list.length-1;i>=0;i--){ const it=list[i]; if(it.x===p.x && it.y===p.y){
      if(it.kind==='heal'){ p.hp = Math.min(5, p.hp+2); state.emit('msg','Healed'); }
      if(it.kind==='shield'){ p.shield = 1; state.emit('msg','Shield up'); }
      if(it.kind==='speed'){ p.haste = 60*5; state.emit('msg','Swift'); }
      list.splice(i,1);
    }}
  }
  global.Powerups = { tryPickup };
})(window);
