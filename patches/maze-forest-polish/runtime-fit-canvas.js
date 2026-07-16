(function(){
  function fitCanvasToCSS(canvas){
    if(!canvas) return;
    const dpr = Math.max(1, window.devicePixelRatio||1);
    const cssW = Math.floor(canvas.clientWidth||canvas.width||0);
    const cssH = Math.floor(canvas.clientHeight||canvas.height||0);
    if (!cssW || !cssH) return; // hidden or not laid out yet
    const needW = cssW * dpr;
    const needH = cssH * dpr;
    if (canvas.width !== needW || canvas.height !== needH){
      canvas.width = needW;
      canvas.height = needH;
    }
    const ctx = canvas.getContext && canvas.getContext('2d');
    if (ctx && ctx.setTransform) ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  function installCanvasFit(canvas){
    const doFit = ()=>fitCanvasToCSS(canvas);
    window.addEventListener('resize', doFit, {passive:true});
    if (document.readyState === 'complete' || document.readyState === 'interactive') setTimeout(doFit,0);
    else window.addEventListener('DOMContentLoaded', doFit, {once:true});
    // First paint
    setTimeout(doFit,0);
  }
  window.fitCanvasToCSS = fitCanvasToCSS;
  window.installCanvasFit = installCanvasFit;
})();
