import asyncio, json, os, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACTS=os.environ.get("ARTIFACTS","/home/james/Hermes/state/workspaces/game-dev/artifacts")
BASE_URL=os.environ.get("BASE_URL","http://localhost:8010")
GAMES=[
    ("maze-forest","/maze-forest/index.html"),
    ("narrative-maze-prototype","/narrative-maze-prototype/index.html"),
]

Path(ARTIFACTS).mkdir(parents=True, exist_ok=True)

async def run_one(pw, name, path):
    url=f"{BASE_URL}{path}"
    browser = await pw.chromium.launch()
    context = await browser.new_context()
    page = await context.new_page()

    logs=[]
    page.on("console", lambda msg: logs.append({"type": msg.type, "text": msg.text}))
    page.on("pageerror", lambda exc: logs.append({"type":"pageerror","text": str(exc)}))

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait a moment for any async init
        await page.wait_for_timeout(1000)
        # Try to find a canvas
        canvas_count = await page.evaluate("document.querySelectorAll('canvas').length")
        # Probe top-left pixel of first canvas if present
        magenta_probe=None
        if canvas_count>0:
            magenta_probe = await page.evaluate(
                """
                (function(){
                  const c=document.querySelector('canvas');
                  if(!c) return null;
                  const ctx=c.getContext('2d');
                  try{
                    const d=ctx.getImageData(10,10,1,1).data; // [r,g,b,a]
                    return {r:d[0],g:d[1],b:d[2],a:d[3], w:c.width, h:c.height};
                  }catch(e){
                    return {error: String(e)};
                  }
                })()
                """
            )
        # Try simple input to trigger movement/UI and verify movement via exposed diag state
        try:
            pos_before = await page.evaluate("(window.__mf_state && window.__mf_state.player) ? {x: window.__mf_state.player.x, y: window.__mf_state.player.y} : null")
            moved=False
            for key in ["ArrowRight","ArrowDown","ArrowLeft","ArrowUp"]:
                await page.keyboard.down(key)
                await page.wait_for_timeout(450)
                await page.keyboard.up(key)
                pos_mid = await page.evaluate("(window.__mf_state && window.__mf_state.player) ? {x: window.__mf_state.player.x, y: window.__mf_state.player.y} : null")
                if pos_before and pos_mid and (pos_mid['x']!=pos_before['x'] or pos_mid['y']!=pos_before['y']):
                    moved=True
                    break
            pos_after = await page.evaluate("(window.__mf_state && window.__mf_state.player) ? {x: window.__mf_state.player.x, y: window.__mf_state.player.y} : null")
        except Exception:
            pos_before = None
            pos_after = None
        # Maze Forest specific checks via exposed state
        mf_checks=None
        try:
            mf_present = await page.evaluate("!!window.__mf_state")
            if mf_present:
                counts_before = await page.evaluate("({ enemies: __mf_state.level.enemies.length, traps: __mf_state.level.traps.length, powerups: __mf_state.level.powerups.length, hp: __mf_state.player.hp, shield: __mf_state.player.shield, haste: __mf_state.player.haste, level: __mf_state.levelNum })")
                pow_pick=None; trap_hit=None; level_up=None
                # Powerup test
                await page.evaluate("(function(){ if(__mf_state.level.powerups.length){ const it=__mf_state.level.powerups[0]; __mf_state.player.x=it.x; __mf_state.player.y=it.y; } })()")
                await page.wait_for_timeout(200)
                after_pow = await page.evaluate("({ powerups: __mf_state.level.powerups.length, hp: __mf_state.player.hp, shield: __mf_state.player.shield, haste: __mf_state.player.haste })")
                pow_pick = after_pow
                # Trap test (force active)
                await page.evaluate("(function(){ if(__mf_state.level.traps.length){ const t=__mf_state.level.traps[0]; t.phase=0; __mf_state.ticks=0; __mf_state.player.shield=0; __mf_state.player.hp=3; __mf_state.player.x=t.x; __mf_state.player.y=t.y; } })()")
                await page.wait_for_timeout(200)
                after_trap = await page.evaluate("({ hp: __mf_state.player.hp, shield: __mf_state.player.shield })")
                trap_hit = after_trap
                # Level up test: move to exit
                before_level = await page.evaluate("__mf_state.levelNum")
                await page.evaluate("(function(){ const ex=__mf_state.level.exit; __mf_state.player.x=ex.x; __mf_state.player.y=ex.y; })()")
                await page.wait_for_timeout(250)
                after_level = await page.evaluate("__mf_state.levelNum")
                level_up = {"before": before_level, "after": after_level}
                mf_checks = {"counts_before": counts_before, "pow_pick": pow_pick, "trap_hit": trap_hit, "level_up": level_up}
        except Exception:
            pass

        # Attempt narrative interactions if narrative state is present
        try:
            if await page.evaluate("!!window.__nm_state"):
                # Teleport adjacent to first story node, then move onto it with a key press to trigger open
                nav = await page.evaluate("(function(){ const s=window.__nm_state; if(!(s && s.level && s.level.storyNodes && s.level.storyNodes.length)) return null; const n=s.level.storyNodes[0]; const r=n.r, c=n.c; const grid=s.level.grid; function can(r,c){ return grid[r]&&grid[r][c]===1; } const opts=[[r-1,c,'ArrowDown'],[r+1,c,'ArrowUp'],[r,c-1,'ArrowRight'],[r,c+1,'ArrowLeft']]; for(let i=0;i<opts.length;i++){ const o=opts[i]; if(can(o[0],o[1])){ s.player={r:o[0], c:o[1]}; return {toR:r,toC:c, key:o[2]}; } } s.player={r:r,c:c}; return {toR:r,toC:c, key:null}; })()")
                if nav and nav.get('key'):
                    await page.keyboard.down(nav['key'])
                    await page.wait_for_timeout(120)
                    await page.keyboard.up(nav['key'])
                    await page.wait_for_timeout(250)
                # Record overlay visibility before click
                vis_before = await page.evaluate("(function(){ const ov=document.getElementById('storyOverlay'); return !!ov && !ov.classList.contains('hidden'); })()")
                # If overlay is open, click first available choice or Continue
                await page.evaluate("(function(){ const overlay=document.getElementById('storyOverlay'); if(!overlay) return; const btn=overlay.querySelector('#storyChoices button, #storyContinue'); if(btn){ btn.click(); } })()")
                await page.wait_for_timeout(200)
                vis_after = await page.evaluate("(function(){ const ov=document.getElementById('storyOverlay'); return !!ov && !ov.classList.contains('hidden'); })()")
        except Exception:
            pass

        # Screenshot
        shot_path = os.path.join(ARTIFACTS, f"{name}.png")
        await page.screenshot(path=shot_path, full_page=True)

        # Collect diagnostics overlay if present
        diag_text = await page.evaluate(
            """
            (function(){
              const el=document.querySelector('[data-diag-overlay], .diag-overlay, #diag, #diagnostics');
              if(!el) return null;
              return el.innerText || el.textContent || null;
            })()
            """
        )

        result={
            "game": name,
            "url": url,
            "canvas_count": canvas_count,
            "magenta_probe": magenta_probe,
            "diag_overlay": diag_text,
            "console": logs[:100],
            "screenshot": shot_path,
        }
        # Narrative checks: whether overlay toggled at least once
        try:
            if await page.evaluate("typeof window.__nm_state!=='undefined'"):
                story_was_open = await page.evaluate("!!document.getElementById('storyOverlay') && !document.getElementById('storyOverlay').classList.contains('hidden')")
                result["nm_story_open_before_click"] = story_was_open
                story_now = await page.evaluate("!!document.getElementById('storyOverlay') && !document.getElementById('storyOverlay').classList.contains('hidden')")
                result["nm_story_open_after_click"] = story_now
        except Exception:
            pass
        # attach movement info if available
        try:
            result["pos_before"]=pos_before
            result["pos_after"]=pos_after
            result["mf_checks"]=mf_checks
        except Exception:
            pass
        return result
    finally:
        await context.close()
        await browser.close()

async def main():
    out=[]
    async with async_playwright() as pw:
        for name, path in GAMES:
            res = await run_one(pw, name, path)
            out.append(res)
    print(json.dumps(out, indent=2))

if __name__=="__main__":
    asyncio.run(main())
