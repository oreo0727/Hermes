// runtime-stability-shim.js
// Fit canvas to CSS × DPR, disable smoothing, and guard drawImage source rects.
// Safe to include multiple times; no globals polluted besides window.MF_*
(function(){
  var w = window;
  w.MF_SHIM = w.MF_SHIM || {};

  function fitCanvas(canvas){
    if(!canvas) return;
    var ctx = canvas.getContext('2d');
    if(!ctx) return;
    var dpr = Math.max(1, w.devicePixelRatio||1);
    var cssW = Math.floor(canvas.clientWidth||canvas.width||720);
    var cssH = Math.floor(canvas.clientHeight||canvas.height||720);
    if(!cssW || !cssH) return;
    canvas.width = Math.max(1, cssW * dpr);
    canvas.height = Math.max(1, cssH * dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.imageSmoothingEnabled = false;
    w.MF_SHIM.dpr = dpr;
  }

  function installCanvasFit(){
    var c = document.getElementById('game');
    if(!c) return;
    fitCanvas(c);
    w.addEventListener('resize', function(){ setTimeout(function(){ fitCanvas(c); }, 0); });
    console.log('[Stability] Canvas DPR-fitted; smoothing disabled');
  }

  // Optional guard around drawImage to clamp invalid source rectangles
  function installDrawGuard(){
    var ctxProto = CanvasRenderingContext2D && CanvasRenderingContext2D.prototype;
    if(!ctxProto || ctxProto.__mf_draw_guard_installed) return;
    var _drawImage = ctxProto.drawImage;
    ctxProto.drawImage = function(img, sx, sy, sw, sh, dx, dy, dw, dh){
      try{
        if(arguments.length===3){
          // drawImage(img, dx, dy) — fine
          return _drawImage.apply(this, arguments);
        }
        if(arguments.length===5){
          // drawImage(img, dx, dy, dw, dh) — fine
          return _drawImage.apply(this, arguments);
        }
        // 9-arg form: clamp source rects
        sx = Math.max(0, Math.floor(sx||0));
        sy = Math.max(0, Math.floor(sy||0));
        sw = Math.max(1, Math.floor(sw||1));
        sh = Math.max(1, Math.floor(sh||1));
        return _drawImage.call(this, img, sx, sy, sw, sh, dx, dy, dw, dh);
      }catch(e){
        // Draw a readable fallback instead of spraying random atlas bits
        this.fillStyle = '#4B7354';
        var _dw = (arguments.length===3? 8 : (dw||16));
        var _dh = (arguments.length===3? 8 : (dh||16));
        this.fillRect(dx||0, dy||0, _dw, _dh);
        console.warn('[Stability] drawImage guarded fallback:', e);
      }
    };
    ctxProto.__mf_draw_guard_installed = true;
    console.log('[Stability] drawImage guard installed');
  }

  function gateSprites(){
    try{ localStorage.setItem('mf_no_sprites','1'); }catch(_){}
    console.log('[Stability] Sprites temporarily gated (mf_no_sprites=1)');
  }

  function boot(){
    installCanvasFit();
    installDrawGuard();
    gateSprites();
    // Restart level if exposed
    var restarted = false;
    if(typeof w.startLevel==='function'){ try{ w.startLevel(1); restarted = true; }catch(_){} }
    console.log('[Stability] Boot complete', {restarted});
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded', boot);
  } else { setTimeout(boot, 0); }
})();
