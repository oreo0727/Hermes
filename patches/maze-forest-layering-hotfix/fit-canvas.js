// Maze Forest: DPR-aware canvas sizing to match CSS box, avoid 0x0 draw
export function fitCanvasToCSS(canvas) {
  const ctx = canvas.getContext('2d');
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const cssW = Math.floor(canvas.clientWidth);
  const cssH = Math.floor(canvas.clientHeight);
  if (!cssW || !cssH) return; // hidden or collapsed; try again later
  const targetW = cssW * dpr;
  const targetH = cssH * dpr;
  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW;
    canvas.height = targetH;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

export function installCanvasFit(canvas) {
  const onResize = () => fitCanvasToCSS(canvas);
  window.addEventListener('resize', onResize);
  // Kick once after layout settles
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(onResize, 0), { once: true });
  } else {
    setTimeout(onResize, 0);
  }
  onResize();
  return () => window.removeEventListener('resize', onResize);
}

// Usage in maze-forest/src/renderer.js (or boot file):
// import { fitCanvasToCSS, installCanvasFit } from './fit-canvas.js';
// const canvas = document.getElementById('game');
// installCanvasFit(canvas);
// ...then proceed with your draw loop.
