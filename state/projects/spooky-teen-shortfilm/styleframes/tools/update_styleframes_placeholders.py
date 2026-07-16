#!/usr/bin/env python3
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = Path('/home/james/Hermes/state/projects/spooky-teen-shortfilm')
V1 = PROJECT_ROOT / 'styleframes' / 'v1'
CONTACT = PROJECT_ROOT / 'styleframes' / 'styleframes_contact_v1.png'
RAW = V1 / 'raw'
RAW.mkdir(parents=True, exist_ok=True)

frames = [
    ('f02', V1/'sf_f02.png'),
    ('f05', V1/'sf_f05.png'),
    ('f07', V1/'sf_f07.png'),
    ('f08', V1/'sf_f08.png'),
    ('f09', V1/'sf_f09.png'),
    ('f10', V1/'sf_f10.png'),
]

try:
    FONT = ImageFont.truetype('DejaVuSans.ttf', 28)
    FONT_L = ImageFont.truetype('DejaVuSans.ttf', 36)
except Exception:
    FONT = ImageFont.load_default()
    FONT_L = ImageFont.load_default()


def save_backup(p: Path):
    if p.exists():
        b = RAW / (p.stem + '_pre_retry3.png')
        if not b.exists():
            p.replace(b)
            # keep a copy as current too
            Image.open(b).save(p)


def overlay_label(im: Image.Image, text: str):
    draw = ImageDraw.Draw(im)
    pad = 14
    try:
        bbox = draw.textbbox((0,0), text, font=FONT)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    except Exception:
        # Fallback approximate width
        tw = int(len(text) * (FONT.size * 0.6 if hasattr(FONT,'size') else 12))
        th = int(FONT.size if hasattr(FONT,'size') else 16)
    rect = [10, 10, 10 + tw + 2*pad, 10 + th + 2*pad]
    draw.rectangle(rect, fill=(0, 0, 0))
    draw.text((10+pad, 10+pad), text, fill=(240,240,240), font=FONT)
    return im


def apply_phones_only(im: Image.Image):
    # global darken
    overlay = Image.new('RGB', im.size, (0,0,0))
    im = Image.blend(im, overlay, 0.35)
    # add five subtle cool-blue phone glows
    draw = ImageDraw.Draw(im, 'RGBA')
    W,H = im.size
    spots = [
        (int(W*0.30), int(H*0.58)),
        (int(W*0.42), int(H*0.55)),
        (int(W*0.52), int(H*0.57)),
        (int(W*0.62), int(H*0.56)),
        (int(W*0.74), int(H*0.58)),
    ]
    for x,y in spots:
        r=26
        draw.ellipse([x-r, y-r, x+r, y+r], fill=(100, 160, 255, 140))
    # slight blur for bloom
    im = im.filter(ImageFilter.GaussianBlur(radius=0.6))
    return im


def process_frames():
    changed = []
    for fid, path in frames:
        if not path.exists():
            continue
        save_backup(path)
        im = Image.open(path).convert('RGB')
        if fid == 'f08':
            im = apply_phones_only(im)
            im = overlay_label(im, 'F08 — WIP OVERLAY — PHONES-ONLY PASS')
            changed.append(str(path))
            im.save(path, 'PNG')
        elif fid == 'f09':
            im = overlay_label(im, 'F09 — WIP OVERLAY — MACRO PASS (NEEDS RE-GEN)')
            changed.append(str(path))
            im.save(path, 'PNG')
        else:
            # leave other finals untouched for this retry
            pass
    return changed


def build_contact():
    # 2 columns x 3 rows grid to match brief explicitly
    COLS, ROWS = 2, 3
    TW, TH = 960, 540
    W, H = COLS*TW, ROWS*TH
    sheet = Image.new('RGB', (W, H), (6, 6, 8))
    order = ['f02','f05','f07','f08','f09','f10']
    for idx, fid in enumerate(order):
        p = V1 / f'sf_{fid}.png'
        if not p.exists():
            continue
        im = Image.open(p).convert('RGB').resize((TW, TH), Image.LANCZOS)
        r, c = divmod(idx, COLS)
        x, y = c*TW, r*TH
        sheet.paste(im, (x,y))
        # Tile label
        draw = ImageDraw.Draw(sheet)
        label = fid.upper()
        draw.rectangle([x+12, y+12, x+140, y+48], fill=(0,0,0))
        draw.text((x+22, y+18), label, fill=(235,235,235), font=FONT)
    sheet.save(CONTACT, 'PNG')
    return str(CONTACT)

if __name__ == '__main__':
    changed = process_frames()
    contact = build_contact()
    print('UPDATED:', '\n'.join(changed))
    print('CONTACT:', contact)
