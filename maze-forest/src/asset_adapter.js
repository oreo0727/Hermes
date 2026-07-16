(function(global){
  function pickAtlasUrl(baseJsonUrl){
    try{
      const dpr = Math.max(1, global.devicePixelRatio||1);
      // Prefer higher-res atlases on high-DPR screens
      if(dpr >= 3) return baseJsonUrl.replace(/\.json(\?.*)?$/, '@3x.json$1');
      if(dpr >= 2) return baseJsonUrl.replace(/\.json(\?.*)?$/, '@2x.json$1');
      return baseJsonUrl;
    }catch(_){ return baseJsonUrl; }
  }
  global.pickAtlasUrl = pickAtlasUrl;
})(window);
