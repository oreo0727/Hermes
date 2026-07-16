from playwright.sync_api import sync_playwright
import sys, json, os

URL = os.environ.get('URL', 'http://localhost:8000/maze-forest/')
SHOT = os.environ.get('SHOT', '/home/james/Hermes/state/workspaces/game-dev/maze_forest_screenshot.png')
TIMEOUT = int(os.environ.get('TIMEOUT_MS','10000'))

logs = {
  'console': [],
  'errors': [],
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1024, 'height': 768})

    page.on('console', lambda m: logs['console'].append({'type': m.type, 'text': m.text}))
    page.on('pageerror', lambda e: logs['errors'].append({'type': 'pageerror', 'text': str(e)}))

    page.goto(URL, wait_until='domcontentloaded', timeout=TIMEOUT)
    # Wait for canvas and at least one animation frame to render
    page.wait_for_selector('canvas#game', timeout=TIMEOUT)
    page.wait_for_timeout(300)  # allow initial render

    # Grab console errors collected so far (also check browser logs after a short delay)
    page.screenshot(path=SHOT, full_page=False)

    # Evaluate some state if exposed
    state = None
    try:
        state = page.evaluate('window.__mf_state || null')
    except Exception:
        state = None

    browser.close()

print(json.dumps({'shot': SHOT, 'logs': logs, 'state': state}))
