from playwright.sync_api import sync_playwright
import os, json

URL = os.environ.get('URL', 'http://localhost:8000/maze-forest/?debug=1')
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1024, 'height': 768})
    logs = []
    page.on('console', lambda m: logs.append({'type': m.type, 'text': m.text}))
    page.goto(URL, wait_until='domcontentloaded', timeout=10000)
    page.wait_for_selector('canvas#game', timeout=10000)
    page.wait_for_timeout(300)
    s1 = page.evaluate('window.__mf_state ? {x: __mf_state.player.x, y: __mf_state.player.y, ticks: __mf_state.ticks} : null')
    # Try moving down for a bit, then right
    page.keyboard.down('ArrowDown')
    page.wait_for_timeout(400)
    page.keyboard.up('ArrowDown')
    page.keyboard.down('ArrowRight')
    page.wait_for_timeout(400)
    page.keyboard.up('ArrowRight')
    page.wait_for_timeout(100)
    s2 = page.evaluate('window.__mf_state ? {x: __mf_state.player.x, y: __mf_state.player.y, ticks: __mf_state.ticks} : null')
    browser.close()
print(json.dumps({'before': s1, 'after': s2, 'logs': logs}))
