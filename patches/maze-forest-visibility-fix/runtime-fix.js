// Drop-in helpers to size the canvas to its CSS box and device pixel ratio.
export function fitCanvasToCSS(canvas) {
  const ctx = canvas.getContext('2d');
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const cssW = Math.floor(canvas.clientWidth);
  const cssH = Math.floor(canvas.clientHeight);
  if (!cssW || !cssH) return; // hidden or not laid out yet
  const targetW = cssW * dpr;
  const targetH = cssH * dpr;
  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW;
    canvas.height = targetH;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
}

export function installCanvasFit(canvas) {
  const apply = () => fitCanvasToCSS(canvas);
  window.addEventListener('resize', apply);
  // Defer one tick to allow CSS layout to settle on first paint
  requestAnimationFrame(apply);
  setTimeout(apply, 50);
  apply();
}

// Usage (in your boot code):
// import { installCanvasFit } from '../patches/maze-forest-visibility-fix/runtime-fix.js';
// const canvas = document.getElementById('game');
// installCanvasFit(canvas);
