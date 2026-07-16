#!/usr/bin/env python3
import os, math, random, json
from PIL import Image, ImageDraw, ImageFilter

# Config
BASE_DIR = "/home/james/Hermes/state/workspaces/creative-dev/assets/maze-forest"
SPRITES_DIR = os.path.join(BASE_DIR, "sprites")
SHEETS_DIR = os.path.join(BASE_DIR, "sheets")
META_DIR = os.path.join(BASE_DIR, "meta")

SIZE = 64  # tile size @1x
PADDING_SAFE = 2  # inner transparent padding to avoid atlas bleeding
CONTENT = SIZE - PADDING_SAFE*2

random.seed(42)

# Palette (approx)
PALETTE = {
    # Greens
    "green_deep": "#0f2a18",
    "green_dark": "#1f3e23",
    "green_mid":  "#3f7f3a",
    "green_light": "#88c057",
    "green_moss": "#a9d96a",
    # Dirt / wood
    "dirt_dark": "#6e4a2a",
    "dirt_mid":  "#9b7848",
    "wood":      "#6a4b2a",
    # Stone
    "stone_dark": "#5e6556",
    "stone_mid":  "#7a806e",
    "stone_light":"#9aa18d",
    "stone_hi":   "#bfc6b2",
    # Metal
    "metal_light": "#c6cbd4",
    "metal_dark":  "#646b74",
    # Accents
    "heart":   "#ff4747",
    "gold":    "#f6c54b",
    "gold_sh": "#d99b2b",
    # Magic
    "shield":     "#56b4ff",
    "lightning":  "#19ccff",
    "crystal":    "#7a2be2",
    "crystal_hi": "#c084fc",
    # UI neutrals
    "ui_bg": "#203022",
}

# Utilities

def hex_to_rgba(h, a=255):
    h = h.lstrip('#')
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return (r, g, b, a)


def new_tile():
    return Image.new('RGBA', (SIZE, SIZE), (0,0,0,0))


def content_box():
    return (PADDING_SAFE, PADDING_SAFE, SIZE-PADDING_SAFE, SIZE-PADDING_SAFE)


def soft_circle(radius):
    # Create a radial soft circle mask
    d = radius*2
    m = Image.new('L', (d, d), 0)
    draw = ImageDraw.Draw(m)
    draw.ellipse((0,0,d,d), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(radius*0.6))
    return m


def paint_soft_blob(im, cx, cy, radius, color, alpha=180, jitter=0):
    col = hex_to_rgba(color, alpha)
    m = soft_circle(radius)
    x = int(cx - radius + (random.randint(-jitter, jitter) if jitter else 0))
    y = int(cy - radius + (random.randint(-jitter, jitter) if jitter else 0))
    blob = Image.new('RGBA', m.size, col)
    # Paste with mask to apply soft edges at position
    im.paste(blob, (x, y), m)


def radial_glow(size, color, inner_alpha=180, outer_alpha=0):
    img = Image.new('RGBA', (size, size), (0,0,0,0))
    cx = cy = size//2
    maxr = size//2
    base = Image.new('L', (size, size), 0)
    px = base.load()
    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            r = math.hypot(dx, dy) / maxr
            a = int(max(0, min(1, 1-r)) * inner_alpha)
            px[x,y] = a
    base = base.filter(ImageFilter.GaussianBlur(size*0.12))
    col = Image.new('RGBA', (size,size), hex_to_rgba(color, 255))
    img.paste(col, (0,0), base)
    return img


def oval_shadow(bounds, strength=120):
    # bounds in content space
    w = bounds[2]-bounds[0]
    h = bounds[3]-bounds[1]
    m = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((0,0,w,h), fill=strength)
    m = m.filter(ImageFilter.GaussianBlur(int(min(w,h)*0.2)))
    rgba = Image.new('RGBA', (w,h), (0,0,0,255))
    out = Image.new('RGBA', (SIZE,SIZE), (0,0,0,0))
    out.paste(rgba, (bounds[0], bounds[1]), m)
    return out


def noisy_fill(im, box, base_color, var_color=None, specks=120, speck_color=None):
    # Base painterly fill using multiple soft blobs
    l, t, r, b = box
    cx, cy = (l+r)//2, (t+b)//2
    for i in range(80):
        rr = random.randint(int(CONTENT*0.08), int(CONTENT*0.22))
        jitter = int(CONTENT*0.05)
        col = base_color if random.random() < 0.7 or not var_color else var_color
        a = random.randint(60, 110)
        paint_soft_blob(im, random.randint(l, r), random.randint(t, b), rr, col, a, jitter)
    # Specks/moss
    if specks and speck_color:
        draw = ImageDraw.Draw(im)
        for _ in range(specks):
            x = random.randint(l+2, r-3)
            y = random.randint(t+2, b-3)
            if random.random() < 0.6:
                draw.ellipse((x, y, x+1, y+1), fill=hex_to_rgba(speck_color, 180))


def rim_highlight(im, box, color, thickness=3, alpha=120, side='top'):
    draw = ImageDraw.Draw(im)
    l,t,r,b = box
    if side=='top':
        for i in range(thickness):
            a = int(alpha * (1 - i/thickness))
            draw.line((l+4, t+i+2, r-4, t+i+2), fill=hex_to_rgba(color, a), width=2)


def save_sprite(img, name):
    path = os.path.join(SPRITES_DIR, f"{name}.png")
    img.save(path, optimize=True)
    return path

# Sprite generators

def gen_floor_variants():
    names = []
    for i in range(1,5):
        img = new_tile()
        box = content_box()
        # Dirt base
        noisy_fill(img, box, PALETTE['dirt_mid'], PALETTE['dirt_dark'], specks=150, speck_color=PALETTE['stone_light'])
        # Moss tufts lightly
        for _ in range(18):
            x = random.randint(box[0]+6, box[2]-6)
            y = random.randint(box[1]+6, box[3]-6)
            paint_soft_blob(img, x, y, random.randint(3,7), PALETTE['green_light'], alpha=160)
        names.append(save_sprite(img, f"terrain/floor-dirt-var{i}"))
    return names


def gen_decals():
    names = []
    # pebble
    img = new_tile(); box=content_box();
    draw = ImageDraw.Draw(img)
    for _ in range(4):
        w = random.randint(6,10); h = random.randint(4,8)
        x = random.randint(box[0]+8, box[2]-8)
        y = random.randint(box[1]+12, box[3]-10)
        draw.ellipse((x,y,x+w,y+h), fill=hex_to_rgba(PALETTE['stone_light'],230))
    names.append(save_sprite(img, "terrain/decals-pebble"))
    # fern
    img = new_tile(); box=content_box(); draw = ImageDraw.Draw(img)
    cx = (box[0]+box[2])//2; cy=(box[1]+box[3])//2
    for i in range(6):
        ang = -70 + i*24
        r = 18
        ex = cx + int(math.cos(math.radians(ang))*r)
        ey = cy + int(math.sin(math.radians(ang))*r)
        draw.line((cx,cy,ex,ey), fill=hex_to_rgba(PALETTE['green_light'],220), width=3)
    names.append(save_sprite(img, "terrain/decals-fern"))
    # flower red
    for col,name in [(PALETTE['heart'], 'flower-red'), (PALETTE['shield'], 'flower-blue')]:
        img = new_tile(); box=content_box(); draw = ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        for i in range(5):
            ang = i*72
            ex = cx + int(math.cos(math.radians(ang))*8)
            ey = cy + int(math.sin(math.radians(ang))*8)
            draw.ellipse((ex-5,ey-5,ex+5,ey+5), fill=hex_to_rgba(col,230))
        draw.ellipse((cx-3,cy-3,cx+3,cy+3), fill=hex_to_rgba(PALETTE['gold'],230))
        names.append(save_sprite(img, f"terrain/decals-{name}"))
    # mushroom (red cap)
    img = new_tile(); box=content_box(); draw = ImageDraw.Draw(img)
    basey = (box[1]+box[3])//2 + 8
    draw.ellipse((box[0]+24, basey-16, box[0]+40, basey), fill=hex_to_rgba(PALETTE['heart'],240))
    draw.rectangle((box[0]+30, basey, box[0]+34, basey+10), fill=hex_to_rgba(PALETTE['stone_light'],240))
    names.append(save_sprite(img, "terrain/decals-mushroom"))
    return names


def gen_wall_faces():
    names = []
    # Simplified walls: top faces N,S,E,W and side N,S,E,W
    for dirc in ['n','s','e','w']:
        img = new_tile(); box=content_box(); draw = ImageDraw.Draw(img)
        l,t,r,b = box
        # top cap band
        if dirc in ['n','s']:
            h = CONTENT//3
            if dirc=='n': band=(l,t,r,t+h)
            else: band=(l,b-h,r,b)
        else:
            w = CONTENT//3
            if dirc=='w': band=(l,t,l+w,b)
            else: band=(r-w,t,r,b)
        # base stones as painterly blobs
        for _ in range(60):
            x = random.randint(band[0]+4, band[2]-4)
            y = random.randint(band[1]+4, band[3]-4)
            rad = random.randint(4,8)
            col = random.choice([PALETTE['green_mid'], PALETTE['green_light'], PALETTE['green_moss']])
            paint_soft_blob(img, x, y, rad, col, alpha=170)
        rim_highlight(img, band, PALETTE['stone_hi'], thickness=3, alpha=90, side='top')
        # AO under the band
        if dirc=='n':
            ao = oval_shadow((l+6, t+CONTENT//3-2, r-6, t+CONTENT//3+10), strength=140)
        elif dirc=='s':
            ao = oval_shadow((l+6, b-CONTENT//3-10, r-6, b-CONTENT//3+2), strength=140)
        elif dirc=='w':
            ao = oval_shadow((l+CONTENT//3-2, t+6, l+CONTENT//3+10, b-6), strength=140)
        else:
            ao = oval_shadow((r-CONTENT//3-10, t+6, r-CONTENT//3+2, b-6), strength=140)
        img = Image.alpha_composite(img, ao)
        names.append(save_sprite(img, f"terrain/wall-top-{dirc}"))
    for dirc in ['n','s','e','w']:
        img = new_tile(); box=content_box(); draw = ImageDraw.Draw(img)
        l,t,r,b = box
        # side face shading slab
        if dirc in ['n','s']:
            h = CONTENT//3
            if dirc=='n': slab=(l,t,r,t+h)
            else: slab=(l,b-h,r,b)
        else:
            w = CONTENT//3
            if dirc=='w': slab=(l,t,l+w,b)
            else: slab=(r-w,t,r,b)
        # darker shade
        draw.rectangle(slab, fill=hex_to_rgba(PALETTE['green_dark'], 180))
        # noise stones
        for _ in range(40):
            x = random.randint(slab[0]+2, slab[2]-2)
            y = random.randint(slab[1]+2, slab[3]-2)
            paint_soft_blob(img, x, y, random.randint(2,4), PALETTE['green_mid'], alpha=150)
        names.append(save_sprite(img, f"terrain/wall-side-{dirc}"))
    return names


def gen_vines_and_door():
    names=[]
    # vines
    for dirc in ['n','e','s','w']:
        img = new_tile(); box=content_box(); draw = ImageDraw.Draw(img)
        l,t,r,b=box
        # hanging strands
        if dirc=='n':
            y=t+3
            for x in range(l+8, r-8, 8):
                h=random.randint(10,22)
                draw.line((x,y,x,y+h), fill=hex_to_rgba(PALETTE['green_light'],200), width=3)
        if dirc=='s':
            y=b-3
            for x in range(l+8, r-8, 8):
                h=random.randint(10,22)
                draw.line((x,y,x,y-h), fill=hex_to_rgba(PALETTE['green_light'],200), width=3)
        if dirc=='w':
            x=l+3
            for y in range(t+8, b-8, 8):
                h=random.randint(10,22)
                draw.line((x,y,x+h,y), fill=hex_to_rgba(PALETTE['green_light'],200), width=3)
        if dirc=='e':
            x=r-3
            for y in range(t+8, b-8, 8):
                h=random.randint(10,22)
                draw.line((x,y,x-h,y), fill=hex_to_rgba(PALETTE['green_light'],200), width=3)
        names.append(save_sprite(img, f"terrain/vine-overhang-{dirc}"))
    # door exit closed/open
    for state in ['closed','open']:
        img = new_tile(); box=content_box(); draw = ImageDraw.Draw(img)
        l,t,r,b = box
        # stone arch
        arch = [ (l+10, b-8), (l+10, t+18), (r-10, t+18), (r-10, b-8) ]
        draw.rounded_rectangle((l+10, t+10, r-10, b-8), radius=10, outline=hex_to_rgba(PALETTE['stone_hi'],200), width=3)
        # wood door
        if state=='closed':
            draw.rounded_rectangle((l+16, t+16, r-16, b-12), radius=6, fill=hex_to_rgba(PALETTE['wood'],230))
            # metal ring
            draw.ellipse(( (l+r)//2-4, (t+b)//2-2, (l+r)//2+4, (t+b)//2+6 ), fill=hex_to_rgba(PALETTE['metal_light'],230))
        else:
            # open: dark void and ajar plank
            draw.rounded_rectangle((l+16, t+16, r-16, b-12), radius=6, fill=hex_to_rgba('#0c0f10',200))
            draw.polygon([(l+18, b-12),(l+18, t+20),(l+30, t+16),(l+30, b-16)], fill=hex_to_rgba(PALETTE['wood'],230))
        names.append(save_sprite(img, f"terrain/door-exit-{state}"))
    return names


def gen_key_frames():
    names=[]
    for i in range(1,5):
        img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2 + [2,0,-2,0][(i-1)%4]
        # ring
        draw.ellipse((cx-10,cy-10,cx,cy), outline=hex_to_rgba(PALETTE['gold'],255), width=5)
        # shaft
        draw.line((cx,cy-2,cx+14,cy-2), fill=hex_to_rgba(PALETTE['gold'],255), width=5)
        # tooth
        draw.rectangle((cx+10,cy, cx+16, cy+6), fill=hex_to_rgba(PALETTE['gold_sh'],255))
        # glow
        g = radial_glow(SIZE, PALETTE['gold'])
        g = g.filter(ImageFilter.GaussianBlur(2))
        img = Image.alpha_composite(img, g)
        names.append(save_sprite(img, f"pickups/key-gold-{i}"))
    return names


def gen_potion_frames():
    names=[]
    for i in range(1,5):
        img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        # bottle
        draw.ellipse((cx-10,cy-8,cx+10,cy+10), fill=hex_to_rgba('#ffffff',220))
        # liquid shimmer
        level = cy + 2 + int(2*math.sin(i/4*math.tau))
        draw.rectangle((cx-10, level, cx+10, cy+10), fill=hex_to_rgba(PALETTE['heart'],220))
        # highlight
        draw.ellipse((cx-4,cy-4,cx+0,cy), fill=hex_to_rgba('#ffffff',160))
        # cork
        draw.rectangle((cx-3,cy-14,cx+3,cy-8), fill=hex_to_rgba(PALETTE['wood'],240))
        names.append(save_sprite(img, f"pickups/potion-red-{i}"))
    return names


def gen_shield_frames():
    names=[]
    for i in range(1,5):
        img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        # shield badge
        r = 14 + [0,1,0,1][(i-1)%4]
        draw.ellipse((cx-r,cy-r,cx+r,cy+r), fill=hex_to_rgba(PALETTE['shield'],210), outline=hex_to_rgba('#ffffff',80), width=3)
        # crest
        draw.rectangle((cx-3, cy-8, cx+3, cy+8), fill=hex_to_rgba('#ffffff',120))
        # pulse glow
        g = radial_glow(SIZE, PALETTE['shield'])
        g.putalpha(g.getchannel('A').point(lambda a: int(a*0.5)))
        img = Image.alpha_composite(img, g)
        names.append(save_sprite(img, f"pickups/shield-blue-{i}"))
    return names


def gen_tile_lightning():
    names=[]
    for i in range(1,4):
        img=new_tile(); box=content_box();
        # base tile plate
        base = Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
        noisy_fill(base, box, PALETTE['stone_mid'], PALETTE['stone_dark'], specks=80, speck_color=PALETTE['stone_hi'])
        # bolt
        draw = ImageDraw.Draw(base)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        bolt = [(cx-8,cy-10),(cx-2,cy-10),(cx-6,cy),(cx+2,cy),(cx-10,cy+14)]
        draw.polygon(bolt, fill=hex_to_rgba(PALETTE['lightning'], 220))
        if i>1:
            g = radial_glow(SIZE, PALETTE['lightning'])
            base = Image.alpha_composite(base, g)
        names.append(save_sprite(base, f"pickups/tile-lightning-{i}"))
    return names


def gen_crystal_and_pedestal():
    names=[]
    # pedestal
    img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
    cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2+10
    draw.rounded_rectangle((cx-12, cy-6, cx+12, cy+2), radius=3, fill=hex_to_rgba(PALETTE['stone_mid'],230))
    names.append(save_sprite(img, "pickups/pedestal"))
    # crystal frames
    for i in range(1,5):
        img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2-4
        scale = 1.0 + 0.06*math.sin((i-1)/4*math.tau)
        w = int(12*scale); h=int(18*scale)
        poly=[(cx,cy-h),(cx+w,cy-4),(cx,cy+h),(cx-w,cy-4)]
        draw.polygon(poly, fill=hex_to_rgba(PALETTE['crystal'],230), outline=hex_to_rgba(PALETTE['crystal_hi'],140))
        g = radial_glow(SIZE, PALETTE['crystal'])
        img = Image.alpha_composite(img, g)
        names.append(save_sprite(img, f"pickups/crystal-purple-{i}"))
    return names


def gen_chest():
    names=[]
    for state in ['closed','open']:
        img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2+6
        # base
        draw.rounded_rectangle((cx-16, cy-8, cx+16, cy+8), radius=6, fill=hex_to_rgba(PALETTE['wood'],230))
        draw.line((cx-16, cy, cx+16, cy), fill=hex_to_rgba(PALETTE['gold_sh'],220), width=3)
        # lid
        if state=='closed':
            draw.rounded_rectangle((cx-16, cy-16, cx+16, cy), radius=8, fill=hex_to_rgba(PALETTE['wood'],230))
        else:
            draw.rounded_rectangle((cx-16, cy-22, cx+10, cy-6), radius=8, fill=hex_to_rgba(PALETTE['wood'],230))
        # lock
        draw.rectangle((cx-3, cy-4, cx+3, cy+2), fill=hex_to_rgba(PALETTE['gold'],230))
        names.append(save_sprite(img, f"pickups/chest-{state}"))
    return names


def gen_coin_frames():
    names=[]
    for i in range(1,5):
        img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        r=12
        # spin illusion by varying width
        w = int(r*(0.6 + 0.4*abs(math.sin(i/4*math.tau))))
        draw.ellipse((cx-w, cy-r, cx+w, cy+r), fill=hex_to_rgba(PALETTE['gold'],240), outline=hex_to_rgba(PALETTE['gold_sh'],200), width=3)
        g = radial_glow(SIZE, PALETTE['gold'])
        img = Image.alpha_composite(img, g)
        names.append(save_sprite(img, f"pickups/coin-gold-{i}"))
    return names


def gen_spikes():
    names=[]
    # plate base
    for i in range(1,5):
        img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
        l,t,r,b=box; cx=(l+r)//2; cy=(t+b)//2
        draw.rounded_rectangle((l+6, t+12, r-6, b-8), radius=6, fill=hex_to_rgba(PALETTE['stone_mid'],220))
        # spikes height by frame
        h=[4,10,14,8][i-1]
        for sx in range(cx-16, cx+20, 8):
            draw.polygon([(sx, cy+8),(sx+6, cy+8),(sx+3, cy+8-h)], fill=hex_to_rgba(PALETTE['metal_light'],230))
        names.append(save_sprite(img, f"hazards/spikes-plate-{i}"))
    # half variant (static low profile)
    img=new_tile(); box=content_box(); draw=ImageDraw.Draw(img)
    l,t,r,b=box; cx=(l+r)//2; cy=(t+b)//2
    draw.rounded_rectangle((l+6, t+20, r-6, b-10), radius=6, fill=hex_to_rgba(PALETTE['stone_mid'],220))
    for sx in range(cx-16, cx+20, 8):
        draw.polygon([(sx, cy+12),(sx+6, cy+12),(sx+3, cy+8)], fill=hex_to_rgba(PALETTE['metal_light'],230))
    names.append(save_sprite(img, "hazards/spikes-plate-half"))
    return names


def gen_hero():
    names=[]
    # base pose generator with slight bob/step
    def frame(kind, i):
        img=new_tile(); box=content_box(); d=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2 + (0 if kind=='idle' else [1,-1,1,-1][(i-1)%4])
        # contact shadow
        sh = oval_shadow((cx-14, cy+10, cx+14, cy+16), strength=120)
        img = Image.alpha_composite(img, sh)
        # body: tunic (blue) and cloak (darker)
        d.ellipse((cx-10, cy-4, cx+10, cy+14), fill=hex_to_rgba('#3a6fb8',235))
        d.ellipse((cx-12, cy-2, cx+12, cy+10), outline=hex_to_rgba('#1e3f6a',120), width=3)
        # head
        d.ellipse((cx-9, cy-18, cx+9, cy-2), fill=hex_to_rgba('#f0d4b6',240))
        # hair (blond)
        d.pieslice((cx-10, cy-20, cx+10, cy), 200, 340, fill=hex_to_rgba('#e8cc72',240))
        # hands/feet hints
        if kind=='walk':
            # simple leg hints
            d.line((cx-6, cy+12, cx-10, cy+18), fill=hex_to_rgba('#1e3f6a',170), width=3)
            d.line((cx+6, cy+12, cx+10, cy+18), fill=hex_to_rgba('#1e3f6a',170), width=3)
        return img
    for i in range(1,5):
        names.append(save_sprite(frame('idle', i), f"player/hero-idle-{i}"))
    for i in range(1,5):
        names.append(save_sprite(frame('walk', i), f"player/hero-walk-{i}"))
    return names


def gen_enemies():
    names=[]
    # skeleton walk
    for i in range(1,5):
        img=new_tile(); box=content_box(); d=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        sh = oval_shadow((cx-14, cy+10, cx+14, cy+16), strength=110)
        img = Image.alpha_composite(img, sh)
        d.ellipse((cx-8, cy-18, cx+8, cy-2), outline=hex_to_rgba(PALETTE['metal_dark'],200), width=3)
        d.rectangle((cx-2, cy-2, cx+2, cy+10), fill=hex_to_rgba(PALETTE['metal_light'],230))
        # limbs hint
        d.line((cx-6, cy+10, cx-12, cy+18), fill=hex_to_rgba(PALETTE['metal_dark'],200), width=3)
        d.line((cx+6, cy+10, cx+12, cy+18), fill=hex_to_rgba(PALETTE['metal_dark'],200), width=3)
        names.append(save_sprite(img, f"enemies/skeleton-walk-{i}"))
    # goblin walk
    for i in range(1,5):
        img=new_tile(); box=content_box(); d=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        sh = oval_shadow((cx-14, cy+10, cx+14, cy+16), strength=110)
        img = Image.alpha_composite(img, sh)
        d.ellipse((cx-9, cy-18, cx+9, cy-2), fill=hex_to_rgba(PALETTE['green_mid'],240))
        d.ellipse((cx-10, cy-4, cx+10, cy+12), fill=hex_to_rgba(PALETTE['green_dark'],235))
        # ears
        d.polygon([(cx-12, cy-14),(cx-18, cy-10),(cx-10, cy-8)], fill=hex_to_rgba(PALETTE['green_mid'],240))
        d.polygon([(cx+12, cy-14),(cx+18, cy-10),(cx+10, cy-8)], fill=hex_to_rgba(PALETTE['green_mid'],240))
        names.append(save_sprite(img, f"enemies/goblin-walk-{i}"))
    return names


def gen_portal_and_glows():
    names=[]
    # portal 8f swirl
    for i in range(1,9):
        img=new_tile(); box=content_box(); d=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        # ring
        d.ellipse((cx-18, cy-18, cx+18, cy+18), outline=hex_to_rgba(PALETTE['crystal_hi'],180), width=4)
        # swirl (rotating arced pies)
        start = (i*40) % 360
        d.pieslice((cx-14, cy-14, cx+14, cy+14), start, start+120, fill=hex_to_rgba(PALETTE['crystal'],200))
        g = radial_glow(SIZE, PALETTE['crystal'])
        img = Image.alpha_composite(img, g)
        names.append(save_sprite(img, f"fx/portal-purple-{i}"))
    # additive glows
    for col,name in [(PALETTE['gold'],'glow-gold'),(PALETTE['shield'],'glow-blue'),('#00f0ff','glow-cyan'),(PALETTE['crystal'],'glow-purple')]:
        g = radial_glow(SIZE, col)
        names.append(save_sprite(g, f"fx/{name}"))
    return names


def gen_ui():
    names=[]
    # heart full/empty
    for kind in ['full','empty']:
        img=new_tile(); box=content_box(); d=ImageDraw.Draw(img)
        cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
        pts=[(cx,cy+10),(cx-16,cy-2),(cx-10,cy-12),(cx,cy-6),(cx+10,cy-12),(cx+16,cy-2)]
        if kind=='full':
            d.polygon(pts, fill=hex_to_rgba(PALETTE['heart'],240))
        else:
            d.polygon(pts, outline=hex_to_rgba(PALETTE['heart'],220))
        names.append(save_sprite(img, f"ui/heart-{kind}"))
    # icon coin/key
    img=new_tile(); box=content_box(); d=ImageDraw.Draw(img)
    cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
    d.ellipse((cx-12, cy-12, cx+12, cy+12), fill=hex_to_rgba(PALETTE['gold'],240), outline=hex_to_rgba(PALETTE['gold_sh'],200), width=3)
    names.append(save_sprite(img, "ui/icon-coin"))
    img=new_tile(); box=content_box(); d=ImageDraw.Draw(img)
    cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
    d.ellipse((cx-10,cy-10,cx,cy), outline=hex_to_rgba(PALETTE['gold'],255), width=5)
    d.line((cx,cy-2,cx+14,cy-2), fill=hex_to_rgba(PALETTE['gold'],255), width=5)
    d.rectangle((cx+10,cy, cx+16, cy+6), fill=hex_to_rgba(PALETTE['gold_sh'],255))
    names.append(save_sprite(img, "ui/icon-key"))
    # portrait frame round
    img=new_tile(); box=content_box(); d=ImageDraw.Draw(img)
    cx=(box[0]+box[2])//2; cy=(box[1]+box[3])//2
    d.ellipse((cx-20, cy-20, cx+20, cy+20), outline=hex_to_rgba(PALETTE['gold'],230), width=6)
    d.ellipse((cx-16, cy-16, cx+16, cy+16), outline=hex_to_rgba(PALETTE['gold_sh'],220), width=3)
    names.append(save_sprite(img, "ui/portrait-frame-round"))
    return names


def ensure_dirs():
    os.makedirs(SPRITES_DIR, exist_ok=True)
    os.makedirs(SHEETS_DIR, exist_ok=True)
    os.makedirs(META_DIR, exist_ok=True)


# Simple grid packer with spacing between sprites to avoid bleeding on sheets
SHEET_SPACING = 2  # spacing between sprites on sheet


def pack_sprites_to_sheet():
    # Collect all sprite PNGs
    paths=[]
    for root,_,files in os.walk(SPRITES_DIR):
        for f in files:
            if f.endswith('.png'):
                paths.append(os.path.join(root,f))
    paths.sort()
    # Load and pack
    sprites=[]
    for p in paths:
        rel = os.path.relpath(p, SPRITES_DIR).replace('\\','/')
        img = Image.open(p).convert('RGBA')
        sprites.append((rel, img))
    n = len(sprites)
    if n==0:
        return None
    cols = min(12, max(1, int(math.ceil(math.sqrt(n)))))
    rows = int(math.ceil(n/cols))
    cell = SIZE + SHEET_SPACING
    W = cols*cell + SHEET_SPACING
    H = rows*cell + SHEET_SPACING
    sheet = Image.new('RGBA', (W,H), (0,0,0,0))
    atlas = {}

    x=y=0; col=0; row=0
    for name,img in sprites:
        px = SHEET_SPACING + col*cell
        py = SHEET_SPACING + row*cell
        sheet.alpha_composite(img, (px, py))
        atlas[name] = {
            "x": px,
            "y": py,
            "w": SIZE,
            "h": SIZE,
            "origin": [0.5, 0.5]
        }
        col += 1
        if col>=cols:
            col=0; row+=1
    # Save sheet @1x and @2x
    sheet_path = os.path.join(SHEETS_DIR, 'spritesheet.png')
    sheet.save(sheet_path, optimize=True)
    sheet2 = sheet.resize((sheet.width*2, sheet.height*2), Image.NEAREST)
    sheet2.save(os.path.join(SHEETS_DIR, 'spritesheet@2x.png'), optimize=True)

    # Build animation group metadata (frames arrays)
    def add_anim(base_name, frame_count):
        frames=[]
        for i in range(1, frame_count+1):
            key = f"{base_name}-{i}.png"
            if key in atlas:
                fr = atlas[key]
                frames.append({"x": fr['x'], "y": fr['y'], "w": fr['w'], "h": fr['h']})
        if frames:
            # also attach frames to first frame entry for convenience
            first_key = f"{base_name}-1.png"
            if first_key in atlas:
                atlas[first_key]['frames'] = frames
            # and dedicated base entry
            atlas[f"{base_name}.anim"] = {"frames": frames, "origin": [0.5,0.5]}

    # Known animations
    add_anim('pickups/key-gold', 4)
    add_anim('pickups/potion-red', 4)
    add_anim('pickups/shield-blue', 4)
    add_anim('pickups/tile-lightning', 3)
    add_anim('pickups/crystal-purple', 4)
    add_anim('pickups/coin-gold', 4)
    add_anim('hazards/spikes-plate', 4)
    add_anim('player/hero-idle', 4)
    add_anim('player/hero-walk', 4)
    add_anim('enemies/skeleton-walk', 4)
    add_anim('enemies/goblin-walk', 4)
    add_anim('fx/portal-purple', 8)

    # Write atlas JSON (paths as names without extension base folder prefix assets/sprites/)
    atlas_json_path = os.path.join(SHEETS_DIR, 'spritesheet.json')
    # Convert keys from 'foo.png' to 'foo'
    cleaned = {}
    for k,v in atlas.items():
        name = k[:-4] if k.endswith('.png') else k
        cleaned[name] = v
    with open(atlas_json_path, 'w') as f:
        json.dump(cleaned, f, indent=2)

    return sheet_path


def gen_palette_swatches():
    # Palette swatch PNG grid and JSON
    keys = [
        'green_deep','green_dark','green_mid','green_light','green_moss',
        'dirt_dark','dirt_mid','wood',
        'stone_dark','stone_mid','stone_light','stone_hi',
        'metal_light','metal_dark','heart','gold','gold_sh','shield','lightning','crystal','crystal_hi'
    ]
    cols=7
    rows=math.ceil(len(keys)/cols)
    cell=32
    W=cols*cell
    H=rows*cell
    img = Image.new('RGBA',(W,H),(0,0,0,0))
    d = ImageDraw.Draw(img)
    for i,k in enumerate(keys):
        r=i//cols; c=i%cols
        x=c*cell; y=r*cell
        d.rectangle((x+2,y+2,x+cell-2,y+cell-2), fill=hex_to_rgba(PALETTE[k],255))
    img.save(os.path.join(META_DIR,'swatches.png'), optimize=True)
    with open(os.path.join(META_DIR,'swatches.json'),'w') as f:
        json.dump({k: PALETTE[k] for k in keys}, f, indent=2)


def write_readme():
    md = f"""
# Maze Forest Asset Pack (Cozy Painterly)

This pack provides painterly, rounded, cozy-forest sprites for a 64x64 base grid (with optional @2x). Assets are hand-crafted via procedural brushes to match a soft, fantasy style with gentle ambient occlusion and readable gameplay silhouettes.

Contents
- sheets/spritesheet.png and sheets/spritesheet@2x.png
- sheets/spritesheet.json (atlas with origin [0.5,0.5], animations listed as <name>.anim entries)
- sprites/ (individual PNGs; each tile includes a 2 px transparent safe border)
- meta/swatches.png and meta/swatches.json (approx palette)

Style and tech
- Painterly textures, rounded forms, soft top-left lighting, AO under walls/props.
- Hazards use higher-contrast/specular metals; magic items glow (purple/blue); loot is warm gold.
- Transparent PNGs, neutral gamma. Padding: 2 px inner safe border and 2 px sheet spacing to avoid atlas bleeding.
- Anchors: centered ([0.5, 0.5]) for all entries.

Naming
- Kebab-case per directories (terrain/, pickups/, hazards/, player/, enemies/, fx/, ui/).
- Animated sequences exported as name-1..N. Atlas also includes <base>.anim with frames[].

Licensing
- Original work by Creative Dev for Project Aetherion.
- Royalty-free, perpetual license for Project Aetherion use across platforms.
- Redistribution outside Project Aetherion permitted only with this README and attribution to Project Aetherion (optional but appreciated).

Usage notes
- Use additive blending for fx/glow_*.
- Animated items are 4–8 frames, loop at 8–12 FPS for cozy feel (portal at ~10–12 FPS).
- Tile-lightning includes base + 2 pulse frames. Spikes-plate is a 4f raise/lower loop; spikes-plate-half is a low-profile static variant.
- Player/enemy sprites are chibi silhouettes with strong separation from greens for readability.

Attribution
- Palette approximations based on provided color guidance.

""".strip()+"\n"
    with open(os.path.join(BASE_DIR,'README.md'),'w') as f:
        f.write(md)


def main():
    ensure_dirs()
    # Generate prioritized set per brief
    gen_floor_variants()
    gen_decals()
    gen_wall_faces()
    gen_vines_and_door()
    gen_key_frames()
    gen_potion_frames()
    gen_shield_frames()
    gen_tile_lightning()
    gen_crystal_and_pedestal()
    gen_chest()
    gen_coin_frames()
    gen_spikes()
    gen_hero()
    gen_enemies()
    gen_portal_and_glows()
    gen_ui()
    gen_palette_swatches()
    pack_sprites_to_sheet()
    write_readme()

if __name__ == '__main__':
    main()
