#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

PROJECT_ROOT = Path('/home/james/Hermes/state/projects/spooky-teen-shortfilm')
V1 = PROJECT_ROOT/'styleframes'/'v1'
RAW = V1/'raw'
V1.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

# 1) f09 macro crop (close-up of fire/logs)
# Strategy: crop a central-lower box (focus where campfire typically sits), then upscale back to 1920x1080.
# Keep an archival copy of the macro crop.

f09_path = V1/'sf_f09.png'
im9 = Image.open(f09_path).convert('RGB')
W,H = im9.size
# Crop box: centered horizontally, lower third vertically
crop_w = int(W*0.42)
crop_h = int(H*0.42)
left = (W - crop_w)//2
# place vertically so it emphasizes the fire area (slightly below center)
top = int(H*0.48 - crop_h//2)
box = (max(0,left), max(0,top), min(W,left+crop_w), min(H, top+crop_h))
macro9 = im9.crop(box)
macro9_arch = RAW/'sf_f09_macro_retry2.png'
macro9_arch.parent.mkdir(parents=True, exist_ok=True)
macro9.save(macro9_arch, 'PNG')
macro9_final = macro9.resize((1920,1080), Image.LANCZOS)
macro9_final.save(f09_path, 'PNG')

# 2) f08 phones-only WIP adjustment
# Strategy: Darken overall, suppress visible fire by overlaying a soft dark vignette centered on the fire region,
# and add subtle cool-blue soft spots to simulate phone-screen light near faces. Label as WIP overlay.

f08_path = V1/'sf_f08.png'
im8 = Image.open(f08_path).convert('RGB')
W8,H8 = im8.size
base8 = ImageEnhance.Brightness(im8).enhance(0.45)  # global darken

# Build a radial dark mask to suppress the fire around lower center
mask = Image.new('L', (W8,H8), 0)
draw_m = ImageDraw.Draw(mask)
# Ellipse parameters around lower center band
cx, cy = W8//2, int(H8*0.66)
rx, ry = int(W8*0.28), int(H8*0.22)
draw_m.ellipse([cx-rx, cy-ry, cx+rx, cy+ry], fill=220)
mask = mask.filter(ImageFilter.GaussianBlur(45))
dark_layer = Image.new('RGB', (W8,H8), (5,5,5))
suppressed = Image.composite(dark_layer, base8, mask)

# Add 3-4 cool-blue soft spots approximating phones held near chests/faces along the arc
spots = Image.new('RGBA', (W8,H8), (0,0,0,0))
draw_s = ImageDraw.Draw(spots)
# Heuristic positions along an arc from left to right
spot_positions = [
    (int(W8*0.30), int(H8*0.63)),
    (int(W8*0.44), int(H8*0.60)),
    (int(W8*0.56), int(H8*0.60)),
    (int(W8*0.70), int(H8*0.62)),
]
for (sx,sy) in spot_positions:
    r = int(min(W8,H8)*0.03)
    draw_s.ellipse([sx-r, sy-r, sx+r, sy+r], fill=(120,170,255,85))
spots = spots.filter(ImageFilter.GaussianBlur(18))
phones_only = suppressed.convert('RGBA')
phones_only.alpha_composite(spots)
phones_only = phones_only.convert('RGB')

# Add WIP corner label
label = Image.new('RGBA', (520,80), (0,0,0,0))
draw_l = ImageDraw.Draw(label)
draw_l.rounded_rectangle([0,0,520,80], radius=14, fill=(0,0,0,155))
draw_l.text((14,18), 'WIP OVERLAY — PHONES-ONLY PASS', fill=(240,240,240,255))
phones_only.paste(label, (24,24), label)

# Archive WIP
f08_wip_arch = RAW/'sf_f08_phones_only_wip_retry2.png'
phones_only.save(f08_wip_arch, 'PNG')
# Overwrite final for this retry (until full re-gen available)
phones_only.save(f08_path, 'PNG')

print('Repaired:', f09_path, '-> macro crop applied and saved')
print('Adjusted:', f08_path, '-> phones-only WIP overlay applied and saved')
