#!/usr/bin/env python3
import os, re, json, math, random
from PIL import Image, ImageDraw, ImageFilter

ROOT = "/home/james/Hermes/state/workspaces/creative-dev/assets/maze-forest"
SPRITES = os.path.join(ROOT, "sprites")
SHEETS = os.path.join(ROOT, "sheets")
META = os.path.join(ROOT, "meta")
SIZE = 64  # base tile size
PAD = 2    # inner transparent border to avoid atlas bleeding

random.seed(42)

# Palette approximations (from brief)
palette = {
    "greens": ["#0f2a18", "#1f3e23", "#3f7f3a", "#88c057", "#a9d96a"],
    "dirt": ["#6e4a2a", "#9b7848"],
    "wood": ["#6a4b2a"],
    "stone": ["#5e6556", "#7a806e", "#9aa18d", "#bfc6b2"],
    "metal": ["#c6cbd4", "#646b74"],
    "accents": {
        "heart": "#ff4747",
        "coin": "#f6c54b",
        "gold_shadow": "#d99b2b"
    },
    "magic": {
        "shield": "#56b4ff",
        "lightning": "#19ccff",
        "crystal": "#7a2be2",
        "crystal_hi": "#c084fc"
    }
}

# Utilities

def new_canvas():
    return Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))

def inset_box(px=PAD):
    return (px, px, SIZE-px-1, SIZE-px-1)


def hex_to_rgba(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0,2,4)) + (a,)


def lerp(a, b, t):
    return a + (b-a)*t


def radial_gradient(size, inner, outer):
    img = Image.new("RGBA", (size, size), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    cx = cy = size/2
    rmax = size/2
    for r in range(int(rmax), -1, -1):
        t = r / rmax
        col = (
            int(lerp(inner[0], outer[0], t)),
            int(lerp(inner[1], outer[1], t)),
            int(lerp(inner[2], outer[2], t)),
            int(lerp(inner[3], outer[3], t))
        )
        bbox = [cx-r, cy-r, cx+r, cy+r]
        draw.ellipse(bbox, fill=col)
    return img


def add_noise(img, strength=10, density=0.12, colors=((0,0,0,15),(255,255,255,10))):
    draw = ImageDraw.Draw(img)
    w,h = img.size
    count = int(w*h*density)
    for _ in range(count):
        x = random.randint(PAD, w-PAD-1)
        y = random.randint(PAD, h-PAD-1)
        col = random.choice(colors)
        draw.point((x,y), fill=col)
    return img


def soft_shadow(img, radius=2):
    return img.filter(ImageFilter.GaussianBlur(radius))


def paint_dirt_variant(variant=1):
    img = new_canvas()
    draw = ImageDraw.Draw(img)
    base = hex_to_rgba(palette['dirt'][0])
    hi = hex_to_rgba(palette['dirt'][1])
    # base painterly fill with gentle radial brighten toward center
    bg = radial_gradient(SIZE, (*base[:3], 255), (*hi[:3], 255))
    img.alpha_composite(bg)
    # speckles: small pebbles and moss flecks
    add_noise(img, density=0.10+0.03*variant)
    # tiny grass/moss specks in lighter green
    g = hex_to_rgba(palette['greens'][3], 140)
    for _ in range(12+variant*4):
        x = random.randint(PAD+2, SIZE-PAD-3)
        y = random.randint(PAD+2, SIZE-PAD-3)
        draw.ellipse((x, y, x+1, y+1), fill=g)
    # subtle vignette
    v = radial_gradient(SIZE, (0,0,0,0), (0,0,0,60))
    img = Image.alpha_composite(img, v)
    return img


def paint_decal(kind):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    if kind == 'pebble':
        col = hex_to_rgba(palette['stone'][2])
        x,y = SIZE//2-6, SIZE//2-3
        d.ellipse((x, y, x+12, y+8), fill=col)
        edge = Image.new('RGBA', (SIZE,SIZE),(0,0,0,0))
        ImageDraw.Draw(edge).ellipse((x, y, x+12, y+8), outline=hex_to_rgba(palette['stone'][3],180), width=1)
        img.alpha_composite(soft_shadow(edge,1))
    elif kind == 'fern':
        g1 = hex_to_rgba(palette['greens'][4], 220)
        g2 = hex_to_rgba(palette['greens'][3], 220)
        cx, cy = SIZE//2, SIZE//2+4
        for i in range(6):
            ang = -60 + i*20
            r = 10 + i
            x2 = cx + int(math.cos(math.radians(ang))*r)
            y2 = cy + int(math.sin(math.radians(ang))*r)
            d.line((cx,cy,x2,y2), fill=g2, width=2)
            for t in range(3, r, 3):
                tx = cx + int(math.cos(math.radians(ang))*t)
                ty = cy + int(math.sin(math.radians(ang))*t)
                ImageDraw.Draw(img).ellipse((tx-1,ty-1,tx+1,ty+1), fill=g1)
    elif kind == 'flower_red':
        petal = hex_to_rgba('#d95050', 230)
        center = hex_to_rgba('#ffe07a', 255)
        cx, cy = SIZE//2, SIZE//2
        for i in range(5):
            ang = i*72
            dx = int(math.cos(math.radians(ang))*6)
            dy = int(math.sin(math.radians(ang))*6)
            d.ellipse((cx-4+dx,cy-4+dy,cx+4+dx,cy+4+dy), fill=petal)
        d.ellipse((cx-3,cy-3,cx+3,cy+3), fill=center)
    elif kind == 'flower_blue':
        petal = hex_to_rgba('#6aa8ff', 230)
        center = hex_to_rgba('#ffe07a', 255)
        cx, cy = SIZE//2, SIZE//2
        for i in range(6):
            ang = i*60
            dx = int(math.cos(math.radians(ang))*5)
            dy = int(math.sin(math.radians(ang))*5)
            d.ellipse((cx-3+dx,cy-3+dy,cx+3+dx,cy+3+dy), fill=petal)
        d.ellipse((cx-3,cy-3,cx+3,cy+3), fill=center)
    elif kind == 'mushroom':
        cap = hex_to_rgba('#e2554a')
        dots = (255,255,255,200)
        stem = hex_to_rgba('#f3e7d7')
        # stem
        d.rounded_rectangle((SIZE//2-3,SIZE//2, SIZE//2+3, SIZE//2+12), radius=2, fill=stem)
        # cap
        d.pieslice((SIZE//2-10,SIZE//2-6,SIZE//2+10,SIZE//2+10), 200, 340, fill=cap)
        for i in range(5):
            rx = random.randint(-7,7)
            ry = random.randint(-4,2)
            d.ellipse((SIZE//2+rx-2, SIZE//2+ry-2, SIZE//2+rx+2, SIZE//2+ry+2), fill=dots)
    return img

# Pickups and items

def paint_key_gold_frame(frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    bob = [0, -1, 0, 1][(frame-1)%4]
    cx, cy = SIZE//2, SIZE//2 + bob
    gold = hex_to_rgba(palette['accents']['coin'])
    shadow = hex_to_rgba(palette['accents']['gold_shadow'])
    # ring
    d.ellipse((cx-10, cy-10, cx, cy), outline=gold, width=3)
    # stem
    d.rectangle((cx, cy-2, cx+12, cy+2), fill=gold)
    # teeth
    d.rectangle((cx+8, cy+2, cx+12, cy+6), fill=gold)
    d.rectangle((cx+4, cy+2, cx+7, cy+6), fill=gold)
    # subtle highlight
    d.arc((cx-10, cy-10, cx, cy), 300, 360, fill=(255,255,255,200), width=2)
    # small AO ellipse
    ao = Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    ImageDraw.Draw(ao).ellipse((cx-8, cy+6, cx+18, cy+12), fill=(0,0,0,80))
    img = Image.alpha_composite(soft_shadow(ao,2), img)
    return img


def paint_potion_red_frame(frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    body = hex_to_rgba('#e33b2f', 210)
    glass = (255,255,255,110)
    glow = (255,90,90,60 + 20*((frame-1)%4))
    # bottle
    d.ellipse((cx-12, cy-8, cx+12, cy+12), fill=body)
    d.rectangle((cx-5, cy-16, cx+5, cy-8), fill=glass)
    d.rounded_rectangle((cx-6, cy-18, cx+6, cy-16), radius=2, fill=glass)
    # glare
    d.pieslice((cx-8, cy-4, cx+8, cy+12), 300, 340, fill=(255,255,255,90))
    # outer glow
    g = radial_gradient(SIZE, (255,0,0,0), glow)
    img = Image.alpha_composite(g, img)
    return img


def paint_shield_blue_frame(frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    core = hex_to_rgba(palette['magic']['shield'])
    rim = (200, 230, 255, 220)
    pulse = 50 + (frame%4)*25
    # shield
    d.polygon([(cx,cy-12),(cx+10,cy-2),(cx,cy+14),(cx-10,cy-2)], fill=core, outline=rim)
    # emblem
    d.polygon([(cx,cy-6),(cx+5,cy-1),(cx,cy+7),(cx-5,cy-1)], fill=(255,255,255,80))
    # glow
    g = radial_gradient(SIZE, (0,0,0,0), (80,170,255,pulse))
    img = Image.alpha_composite(g, img)
    return img


def paint_tile_lightning_frame(frame):
    # 1 static + 2 pulse
    img = new_canvas()
    d = ImageDraw.Draw(img)
    base = paint_dirt_variant(2)
    img.alpha_composite(base)
    cx, cy = SIZE//2, SIZE//2
    bolt = hex_to_rgba(palette['magic']['lightning'])
    # draw simple zig bolt
    path = [(cx-10,cy-14),(cx-2,cy-6),(cx-8,cy-6),(cx+2,cy+6),(cx-2,cy+6),(cx+8,cy+16)]
    d.line(path, fill=bolt, width=4, joint="curve")
    if frame>1:
        g = radial_gradient(SIZE,(0,0,0,0),(80,200,255, 80 if frame==2 else 120))
        img = Image.alpha_composite(g, img)
    return img


def paint_crystal_purple_frame(frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    core = hex_to_rgba(palette['magic']['crystal'])
    hi = hex_to_rgba(palette['magic']['crystal_hi'])
    # crystal body
    pts = [(cx,cy-14),(cx+8,cy-2),(cx+4,cy+12),(cx-4,cy+12),(cx-8,cy-2)]
    d.polygon(pts, fill=core)
    d.line(pts+[pts[0]], fill=hi, width=2)
    # pulse glow
    pulse = [40,80,120,80][(frame-1)%4]
    g = radial_gradient(SIZE,(0,0,0,0),(170, 80, 255, pulse))
    img = Image.alpha_composite(g, img)
    # AO under
    ao = Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    ImageDraw.Draw(ao).ellipse((cx-10, cy+8, cx+10, cy+14), fill=(0,0,0,90))
    img = Image.alpha_composite(soft_shadow(ao,2), img)
    return img


def paint_crystal_pedestal():
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2+8
    stone = hex_to_rgba(palette['stone'][1])
    edge = hex_to_rgba(palette['stone'][3])
    d.rounded_rectangle((cx-12,cy-6,cx+12,cy+6), radius=4, fill=stone, outline=edge)
    d.line((cx-8,cy,cx+8,cy), fill=edge, width=1)
    return img


def paint_coin_gold_frame(frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    gold = hex_to_rgba(palette['accents']['coin'])
    shadow = hex_to_rgba(palette['accents']['gold_shadow'])
    phase = (frame-1)%4
    w,h = (20,20) if phase in (0,2) else (14,22)
    d.ellipse((cx-w//2, cy-h//2, cx+w//2, cy+h//2), fill=gold, outline=shadow, width=2)
    d.arc((cx-w//2+4, cy-h//2+4, cx+w//2-4, cy+h//2-4), 300, 360, fill=(255,255,255,180), width=2)
    return img

# Hazards

def paint_spikes_plate_frame(frame, half=False):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    # plate
    plate = hex_to_rgba(palette['metal'][1])
    d.rounded_rectangle(inset_box(8), radius=6, fill=plate)
    # spikes
    levels = [0, 6, 12, 6]
    rise = 6 if half else levels[(frame-1)%4]
    cols = [16, 32, 48]
    for x in cols:
        basey = SIZE//2 + 6
        h = rise if not half else 6
        pts = [(x, basey-h), (x-6, basey), (x+6, basey)]
        d.polygon(pts, fill=hex_to_rgba(palette['metal'][0]))
    # AO
    ao = Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    ImageDraw.Draw(ao).ellipse((12, 44, 52, 52), fill=(0,0,0,80))
    img = Image.alpha_composite(soft_shadow(ao,2), img)
    return img

# Characters (simple stylized top-down figures)

def paint_hero_frame(kind, frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    body = hex_to_rgba('#c49a6c')  # warm skin
    tunic = hex_to_rgba('#2e6a9a')  # blue tunic for contrast vs green ground
    hair = hex_to_rgba('#d8b36a')
    # bob/walk offset
    off = 0
    if kind == 'idle':
        off = [0,-1,0,1][(frame-1)%4]
    elif kind == 'walk':
        off = [0,-1,0,1][(frame-1)%4]
    cy += off
    # body
    d.ellipse((cx-6, cy-2, cx+6, cy+12), fill=tunic)
    # head
    d.ellipse((cx-6, cy-14, cx+6, cy-2), fill=body)
    # hair cap
    d.pieslice((cx-7, cy-16, cx+7, cy-4), 200, 340, fill=hair)
    # legs animated
    if kind == 'walk':
        phase = (frame-1)%4
        la = -6 if phase in (1,) else 0
        ra = -6 if phase in (3,) else 0
        d.rectangle((cx-5, cy+10, cx-1, cy+16+la), fill=hex_to_rgba('#3b3b3b'))
        d.rectangle((cx+1, cy+10, cx+5, cy+16+ra), fill=hex_to_rgba('#3b3b3b'))
    else:
        d.rectangle((cx-5, cy+10, cx-1, cy+16), fill=hex_to_rgba('#3b3b3b'))
        d.rectangle((cx+1, cy+10, cx+5, cy+16), fill=hex_to_rgba('#3b3b3b'))
    # small cape highlight
    d.rectangle((cx-6, cy+2, cx-2, cy+6), fill=(255,255,255,40))
    return img


def paint_skeleton_frame(frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    bone = hex_to_rgba('#e6e6e6')
    dark = hex_to_rgba('#9a9a9a')
    # skull
    d.ellipse((cx-6, cy-14, cx+6, cy-2), fill=bone, outline=dark)
    d.ellipse((cx-3, cy-10, cx-1, cy-8), fill=dark)
    d.ellipse((cx+1, cy-10, cx+3, cy-8), fill=dark)
    # ribs
    d.ellipse((cx-6, cy-2, cx+6, cy+12), outline=dark, width=2)
    # legs walk
    phase = (frame-1)%4
    la = -6 if phase in (1,) else 0
    ra = -6 if phase in (3,) else 0
    d.rectangle((cx-5, cy+10, cx-1, cy+16+la), fill=dark)
    d.rectangle((cx+1, cy+10, cx+5, cy+16+ra), fill=dark)
    return img


def paint_goblin_frame(frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    g = hex_to_rgba('#3f7f3a')
    hi = hex_to_rgba('#88c057')
    # head with ears
    d.ellipse((cx-7, cy-12, cx+7, cy+0), fill=g)
    d.polygon([(cx-9,cy-6),(cx-3,cy-4),(cx-7,cy)], fill=g)
    d.polygon([(cx+9,cy-6),(cx+3,cy-4),(cx+7,cy)], fill=g)
    # body
    d.ellipse((cx-6, cy, cx+6, cy+12), fill=g)
    # legs walk
    phase = (frame-1)%4
    la = -6 if phase in (1,) else 0
    ra = -6 if phase in (3,) else 0
    d.rectangle((cx-5, cy+10, cx-1, cy+16+la), fill=hi)
    d.rectangle((cx+1, cy+10, cx+5, cy+16+ra), fill=hi)
    return img

# FX

def paint_portal_frame(frame):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    base = hex_to_rgba(palette['magic']['crystal'])
    ring = hex_to_rgba(palette['magic']['crystal_hi'])
    # swirl angle
    ang = (frame-1)*360/8
    for r in range(6, 18, 3):
        a0 = ang + r*10
        d.arc((cx-r,cy-r,cx+r,cy+r), a0, a0+200, fill=ring, width=2)
    # outer glow
    g = radial_gradient(SIZE,(0,0,0,0),(140, 60, 255, 110))
    img = Image.alpha_composite(g, img)
    # rim
    d.ellipse((cx-16,cy-16,cx+16,cy+16), outline=ring, width=2)
    return img


def paint_glow(color_hex):
    img = new_canvas()
    c = hex_to_rgba(color_hex)
    col = (c[0], c[1], c[2], 110)
    g = radial_gradient(SIZE,(0,0,0,0),col)
    return g

# UI

def paint_heart(full=True):
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    col = hex_to_rgba(palette['accents']['heart'] if full else '#5b5b5b')
    # simple heart
    d.pieslice((cx-16,cy-6,cx,cy+10), 180, 360, fill=col)
    d.pieslice((cx,cy-6,cx+16,cy+10), 180, 360, fill=col)
    d.polygon([(cx-16,cy+2),(cx+16,cy+2),(cx,cy+18)], fill=col)
    if not full:
        d.line((cx-14,cy+2,cx+14,cy+2), fill=(0,0,0,60), width=3)
    return img


def paint_icon_coin():
    return paint_coin_gold_frame(1)


def paint_icon_key():
    return paint_key_gold_frame(1)


def paint_portrait_frame_round():
    img = new_canvas()
    d = ImageDraw.Draw(img)
    cx, cy = SIZE//2, SIZE//2
    d.ellipse((cx-20,cy-20,cx+20,cy+20), outline=hex_to_rgba('#c6cbd4'), width=4)
    d.ellipse((cx-22,cy-22,cx+22,cy+22), outline=hex_to_rgba('#646b74',180), width=2)
    return img

# Save helpers

def save(img, relpath):
    path = os.path.join(SPRITES, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, format='PNG')
    return path

# Build list and generate

atlas_entries = {}  # name -> {x,y,w,h} or {frames:[...]} all with origin
frame_images = []   # (name, path)

# Terrain: floors and decals
for i in range(1,5):
    name = f"terrain/floor_dirt_var{i}.png"
    save(paint_dirt_variant(i), name)

for deco in ['pebble','fern','flower_red','flower_blue','mushroom']:
    name = f"terrain/decals_{deco}.png"
    save(paint_decal(deco), name)

# Pickups animations
for i in range(1,5):
    save(paint_key_gold_frame(i), f"pickups/key_gold_{i}.png")
    save(paint_potion_red_frame(i), f"pickups/potion_red_{i}.png")
    save(paint_shield_blue_frame(i), f"pickups/shield_blue_{i}.png")
    save(paint_crystal_purple_frame(i), f"pickups/crystal_purple_{i}.png")

# tile_lightning: 1 static + 2 pulse (we export 3 frames under same base)
for i in range(1,4):
    save(paint_tile_lightning_frame(i), f"pickups/tile_lightning_{i}.png")

# crystal pedestal
save(paint_crystal_pedestal(), "pickups/crystal_pedestal.png")

# coin spin 4f
for i in range(1,5):
    save(paint_coin_gold_frame(i), f"pickups/coin_gold_{i}.png")

# Hazards spikes
for i in range(1,5):
    save(paint_spikes_plate_frame(i, half=False), f"hazards/spikes_plate_{i}.png")
save(paint_spikes_plate_frame(1, half=True), f"hazards/spikes_plate_half.png")

# Player idle/walk
for i in range(1,5):
    save(paint_hero_frame('idle', i), f"player/hero_idle_{i}.png")
    save(paint_hero_frame('walk', i), f"player/hero_walk_{i}.png")

# Enemies walk
for i in range(1,5):
    save(paint_skeleton_frame(i), f"enemies/skeleton_walk_{i}.png")
    save(paint_goblin_frame(i), f"enemies/goblin_walk_{i}.png")

# FX portal 8f and glows
for i in range(1,9):
    save(paint_portal_frame(i), f"fx/portal_purple_{i}.png")

save(paint_glow(palette['accents']['coin']), "fx/glow_gold.png")
save(paint_glow(palette['magic']['shield']), "fx/glow_blue.png")
save(paint_glow('#00ffff'), "fx/glow_cyan.png")
save(paint_glow(palette['magic']['crystal']), "fx/glow_purple.png")

# UI
save(paint_heart(True), "ui/heart_full.png")
save(paint_heart(False), "ui/heart_empty.png")
save(paint_icon_coin(), "ui/icon_coin.png")
save(paint_icon_key(), "ui/icon_key.png")
save(paint_portrait_frame_round(), "ui/portrait_frame_round.png")

# Pack atlas
# Collect all sprite files
sprite_files = []
for base, _, files in os.walk(SPRITES):
    for f in files:
        if f.endswith('.png'):
            path = os.path.join(base, f)
            rel = os.path.relpath(path, SPRITES)
            name = rel[:-4]  # without .png
            sprite_files.append((name, path))

# Simple shelf pack into a square-ish sheet
W = 1024
x = y = 0
row_h = 0
sheet = Image.new('RGBA', (W, W), (0,0,0,0))
positions = {}

for name, path in sorted(sprite_files):
    img = Image.open(path).convert('RGBA')
    w, h = img.size
    if x + w > W:
        x = 0
        y += row_h
        row_h = 0
    if y + h > W:
        # grow sheet (rare for this set). Double height.
        newH = max(y+h, sheet.size[1]*2)
        ns = Image.new('RGBA', (W, newH), (0,0,0,0))
        ns.paste(sheet, (0,0))
        sheet = ns
    sheet.paste(img, (x,y), img)
    positions[name] = (x,y,w,h)
    x += w
    row_h = max(row_h, h)

# Save sheet(s)
sheet_path = os.path.join(SHEETS, 'spritesheet.png')
sheet.save(sheet_path, format='PNG')
# 2x sheet
sheet2x = sheet.resize((sheet.size[0]*2, sheet.size[1]*2), Image.Resampling.NEAREST)
sheet2x_path = os.path.join(SHEETS, 'spritesheet@2x.png')
sheet2x.save(sheet2x_path, format='PNG')

# Build atlas JSON with grouped frames
atlas = {"meta": {
    "tile_size": SIZE,
    "sheet": os.path.relpath(sheet_path, ROOT).replace('\\','/'),
    "sheet@2x": os.path.relpath(sheet2x_path, ROOT).replace('\\','/'),
    "origin": [0.5, 0.5]
}, "sprites": {}}

# Group names with _N suffix
anim_groups = {}
for name, (x,y,w,h) in positions.items():
    m = re.match(r"^(.*)_([0-9]+)$", name)
    if m:
        base = m.group(1)
        anim_groups.setdefault(base, []).append((int(m.group(2)), x,y,w,h))
    else:
        atlas['sprites'][name] = {"x": x, "y": y, "w": w, "h": h, "origin": [0.5,0.5]}

# Sort frames and insert
for base, frames in anim_groups.items():
    frames_sorted = sorted(frames, key=lambda t: t[0])
    atlas['sprites'][base] = {
        "frames": [{"x": fx, "y": fy, "w": fw, "h": fh} for _,fx,fy,fw,fh in frames_sorted],
        "origin": [0.5,0.5]
    }

# Save atlas
with open(os.path.join(META, 'spritesheet.json'), 'w') as f:
    json.dump(atlas, f, indent=2)

# Palette swatch PNG and JSON
swatch = Image.new('RGBA', (SIZE*5, SIZE*4), (0,0,0,0))
labels = []
# assemble ordered list of colors
cols = [
    ("greens_0", palette['greens'][0]),
    ("greens_1", palette['greens'][1]),
    ("greens_2", palette['greens'][2]),
    ("greens_3", palette['greens'][3]),
    ("greens_4", palette['greens'][4]),
    ("dirt_0", palette['dirt'][0]),
    ("dirt_1", palette['dirt'][1]),
    ("wood_0", palette['wood'][0]),
    ("stone_0", palette['stone'][0]),
    ("stone_1", palette['stone'][1]),
    ("stone_2", palette['stone'][2]),
    ("stone_3", palette['stone'][3]),
    ("metal_0", palette['metal'][0]),
    ("metal_1", palette['metal'][1]),
    ("heart", palette['accents']['heart']),
    ("coin", palette['accents']['coin']),
    ("gold_shadow", palette['accents']['gold_shadow']),
    ("shield", palette['magic']['shield']),
    ("lightning", palette['magic']['lightning']),
    ("crystal", palette['magic']['crystal']),
    ("crystal_hi", palette['magic']['crystal_hi'])
]
for idx,(name,hexv) in enumerate(cols):
    x = (idx % 5) * SIZE
    y = (idx // 5) * SIZE
    ImageDraw.Draw(swatch).rectangle((x+PAD,y+PAD,x+SIZE-PAD-1,y+SIZE-PAD-1), fill=hex_to_rgba(hexv))
    labels.append({"name": name, "hex": hexv})

swatch.save(os.path.join(META, 'palette.png'), format='PNG')
with open(os.path.join(META, 'swatches.json'), 'w') as f:
    json.dump(labels, f, indent=2)

print("Generated sprites, sheets, and meta.")
