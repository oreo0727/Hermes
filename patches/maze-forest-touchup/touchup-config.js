(function(){
  // Visual knobs (safe defaults). Override per your taste.
  window.MAZE_OPTS = Object.assign({}, window.MAZE_OPTS||{}, {
    targetTile: 80,                  // desired tile in CSS px; code will snap to a crisp nearby size
    entity: {
      player: 0.96,                 // fraction of tile
      enemy: 0.86,
      powerup: 0.78,
      trap: 0.68
    },
    exit: {
      glowAlpha: 0.30,              // additive glow opacity
      glowScale: 1.15               // glow radius factor relative to tile
    },
    vignette: {
      strength: 0.35,               // lower than current — stop crushing edges
      radius: 0.90
    },
    floor: {
      tint: 'rgba(0,0,0,0.10)',     // calm busy floor with a subtle dark tint
      desaturate: 0.15              // if your renderer supports HSL/HSV tinting
    }
  });
})();
