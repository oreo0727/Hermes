(function(global){
  function isActive(trap, ticks){ return ((ticks + trap.phase) % 60) < 30; }
  function checkTrapDamage(state){
    const p = state.player; const key = p.x+","+p.y;
    for(const t of state.level.traps){
      if(t.x===p.x && t.y===p.y && isActive(t, state.ticks)){
        if(state.player.shield>0){ state.player.shield = 0; state.emit('msg','Shield broke!'); }
        else { state.player.hp = Math.max(0, state.player.hp-1); state.emit('msg','Ouch!'); }
      }
    }
  }
  global.Traps = { isActive, checkTrapDamage };
})(window);
