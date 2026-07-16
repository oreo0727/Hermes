(function(){
  // Runtime knobs for Maze Forest polish
  window.MAZE_OPTS = Object.assign({
    // Desired on-screen tile size in CSS px; renderer will snap to a nearby crisp size
    targetTile: 72,
    // Make entities fill more of the tile without touching borders
    entityScale: 1.2,
    // Slightly stronger shadows for a grounded look when scaled up
    shadowScale: 1.2,
    // 0..1 how strong the vignette overlay should appear
    vignetteStrength: 0.5
  }, window.MAZE_OPTS || {});
})();
