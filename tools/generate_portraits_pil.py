#!/usr/bin/env python
"""Fallback Pillow: ritratti stilizzati curati 320x320 + sfondi title/ending 1280x720.

Uso:
    python tools/generate_portraits_pil.py [nomi...] | --all
Stile: busto anime semplificato con gradiente + anello glow, capelli a ciocche,
occhi grandi a 3 tonalita', ombra cel, lineart scura.
"""
import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
PORTRAITS_DIR = ROOT / "assets" / "portraits"
BACKGROUNDS_DIR = ROOT / "assets" / "backgrounds"

S = 4  # supersampling
W = H = 320

LINE = (34, 28, 42, 255)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def v_gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=lerp(top, bottom, y / max(1, h - 1)))
    return img


CHARS = {
    "kaira": dict(
        skin=(255, 219, 186), hair=(214, 64, 48), hair_dark=(158, 38, 30),
        uniform=(24, 128, 132), uniform2=(236, 122, 40), collar=(236, 122, 40),
        eyes=(46, 140, 130), bg1=(18, 62, 74), bg2=(8, 22, 34), glow=(90, 220, 210),
        gender="f", hair_style="short_wavy", mouth="smirk", extra=[],
    ),
    "ilan": dict(
        skin=(216, 178, 138), hair=(52, 42, 46), hair_dark=(30, 24, 28),
        uniform=(96, 74, 58), uniform2=(58, 70, 92), collar=(58, 70, 92),
        eyes=(96, 72, 48), bg1=(60, 50, 74), bg2=(20, 16, 32), glow=(196, 168, 240),
        gender="m", hair_style="tied_back", mouth="soft", extra=["glasses"],
    ),
    "sette": dict(
        skin=(238, 240, 248), hair=(224, 230, 244), hair_dark=(148, 168, 210),
        uniform=(210, 218, 236), uniform2=(58, 96, 190), collar=(58, 96, 190),
        eyes=(255, 178, 40), bg1=(24, 40, 88), bg2=(8, 12, 34), glow=(90, 150, 255),
        gender="a", hair_style="android", mouth="calm", extra=["plates"],
    ),
    "naia": dict(
        skin=(126, 84, 60), hair=(38, 158, 142), hair_dark=(22, 104, 96),
        uniform=(46, 110, 74), uniform2=(120, 220, 170), collar=(120, 220, 170),
        eyes=(70, 180, 150), bg1=(20, 74, 52), bg2=(6, 26, 22), glow=(140, 255, 190),
        gender="f", hair_style="bun", mouth="smile", extra=["freckles", "flowers"],
    ),
    "ada": dict(
        skin=(246, 214, 189), hair=(198, 198, 206), hair_dark=(140, 140, 152),
        uniform=(232, 236, 240), uniform2=(190, 60, 70), collar=(190, 60, 70),
        eyes=(110, 90, 70), bg1=(70, 62, 66), bg2=(26, 22, 26), glow=(255, 210, 180),
        gender="f", hair_style="bun", mouth="soft", extra=["age"],
    ),
    "bruno": dict(
        skin=(226, 172, 128), hair=(88, 58, 36), hair_dark=(56, 36, 22),
        uniform=(180, 120, 40), uniform2=(90, 90, 100), collar=(90, 90, 100),
        eyes=(80, 60, 40), bg1=(72, 52, 30), bg2=(26, 18, 12), glow=(255, 190, 90),
        gender="m", hair_style="bandana", mouth="grin", extra=["beard"],
    ),
    "luce": dict(
        skin=(255, 226, 200), hair=(150, 96, 52), hair_dark=(104, 62, 32),
        uniform=(250, 214, 90), uniform2=(90, 160, 220), collar=(90, 160, 220),
        eyes=(120, 170, 220), bg1=(255, 200, 120), bg2=(240, 130, 110), glow=(255, 250, 200),
        gender="c", hair_style="pigtails", mouth="big_smile", extra=[],
    ),
    "custode": dict(
        skin=(80, 150, 230), hair=(60, 110, 210), hair_dark=(30, 60, 150),
        uniform=(30, 60, 130), uniform2=(90, 200, 255), collar=(90, 200, 255),
        eyes=(180, 240, 255), bg1=(10, 20, 50), bg2=(2, 4, 16), glow=(80, 170, 255),
        gender="h", hair_style="holo", mouth="line", extra=["holo"],
    ),
}


def draw_background(d, w, h, c):
    for y in range(h):
        d.line([(0, y), (w, y)], fill=lerp(c["bg1"], c["bg2"], y / (h - 1)))


def glow_ring(img, c):
    w, h = img.size
    ring = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    cx, cy, r = w // 2, int(h * 0.42), int(w * 0.36)
    for i, alpha in ((0, 190), (10, 120), (22, 60)):
        rd.ellipse([cx - r - i, cy - r - i, cx + r + i, cy + r + i],
                   outline=c["glow"] + (alpha,), width=6 + i // 2)
    ring = ring.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(ring)


def draw_bust(d, w, h, c):
    """Spalle + torso con colletto."""
    cx = w // 2
    top = int(h * 0.62)
    # spalle: curva
    shoulder_w = int(w * 0.42) if c["gender"] != "c" else int(w * 0.33)
    pts = [(cx - shoulder_w, h), (cx - shoulder_w, top + int(h * 0.10))]
    for t in range(21):
        a = math.pi * t / 20
        x = cx - shoulder_w * math.cos(a)
        y = top + int(h * 0.10) - math.sin(a) * int(h * 0.10)
        pts.append((x, y))
    pts += [(cx + shoulder_w, h)]
    d.polygon(pts, fill=c["uniform"], outline=LINE, width=S * 2)
    # colletto a V
    col_w = int(w * 0.13)
    d.polygon([(cx - col_w, top + int(h * 0.02)), (cx, top + int(h * 0.14)),
               (cx + col_w, top + int(h * 0.02)),
               (cx + col_w + S * 4, top + int(h * 0.05)),
               (cx, top + int(h * 0.19)),
               (cx - col_w - S * 4, top + int(h * 0.05))],
              fill=c["collar"], outline=LINE, width=S * 2)
    # dettaglio uniforme: banda diagonale
    d.line([(cx - shoulder_w + S * 6, h - int(h * 0.08)),
            (cx - int(w * 0.06), top + int(h * 0.16))],
           fill=c["uniform2"], width=S * 4)
    # collo
    neck_w = int(w * 0.075)
    d.rectangle([cx - neck_w, int(h * 0.56), cx + neck_w, top + int(h * 0.06)],
                fill=c["skin"], outline=None)
    # ombra cel sul collo
    d.rectangle([cx - neck_w, int(h * 0.56), cx + neck_w, int(h * 0.60)],
                fill=lerp(c["skin"], (0, 0, 0), 0.25))
    d.line([(cx - neck_w, int(h * 0.56)), (cx - neck_w, top + int(h * 0.05))], fill=LINE, width=S * 2)
    d.line([(cx + neck_w, int(h * 0.56)), (cx + neck_w, top + int(h * 0.05))], fill=LINE, width=S * 2)


def face_polygon(cx, cy, rw, rh, c):
    """Ovale con mascella definita: piu' stretto in basso, mento leggermente a punta."""
    pts = []
    jaw = 0.86 if c["gender"] in ("m",) else 0.78
    for t in range(73):
        a = 2 * math.pi * t / 72
        x = math.sin(a)
        y = -math.cos(a)
        if y > 0.15:  # parte bassa: mascella
            x *= (1.0 - (y - 0.15) * (1 - jaw) * 2.2)
            if y > 0.8:
                x *= 0.72  # mento
        pts.append((cx + x * rw, cy + y * rh))
    return pts


def draw_face(d, w, h, c):
    cx, cy = w // 2, int(h * 0.40)
    rw, rh = int(w * 0.21), int(h * 0.235)
    if c["gender"] == "c":
        rw, rh = int(w * 0.215), int(h * 0.215)  # viso piu' tondo
    pts = face_polygon(cx, cy, rw, rh, c)
    d.polygon(pts, fill=c["skin"], outline=LINE, width=S * 2)
    # ombra cel sotto la mascella (sul collo gia' disegnato) e lato viso
    shade = lerp(c["skin"], (30, 20, 40), 0.18)
    d.polygon([(cx - rw * 0.5, cy + rh * 0.78), (cx, cy + rh * 1.0),
               (cx + rw * 0.5, cy + rh * 0.78), (cx, cy + rh * 0.9)],
              fill=shade)
    # orecchie
    er = int(rw * 0.16)
    for sx in (-1, 1):
        ex = cx + sx * rw
        d.ellipse([ex - er, cy - er, ex + er, cy + er], fill=c["skin"], outline=LINE, width=S * 2)
    return cx, cy, rw, rh


def draw_eyes(d, cx, cy, rw, rh, c):
    ey = cy + int(rh * 0.12)
    ex_off = int(rw * 0.45)
    ew, eh = int(rw * 0.30), int(rh * 0.20)
    if c["gender"] == "c":
        ew, eh = int(rw * 0.34), int(rh * 0.26)  # occhi piu' grandi da bambina
    iris = c["eyes"]
    iris_dark = lerp(iris, (0, 0, 0), 0.5)
    iris_light = lerp(iris, (255, 255, 255), 0.45)
    for sx in (-1, 1):
        x = cx + sx * ex_off
        # bianco
        d.ellipse([x - ew, ey - eh, x + ew, ey + eh], fill=(250, 250, 252), outline=LINE, width=S * 2)
        # iride 3 tonalita'
        ir = int(eh * 0.92)
        d.ellipse([x - ir, ey - ir, x + ir, ey + ir], fill=iris_dark)
        d.ellipse([x - ir + S * 2, ey - ir + S * 2, x + ir - S, ey + ir - S * 3], fill=iris)
        d.ellipse([x - ir // 2, ey - S, x + ir // 2, ey + ir - S * 2], fill=iris_light)
        # pupilla + riflesso
        pr = int(ir * 0.42)
        d.ellipse([x - pr, ey - pr, x + pr, ey + pr], fill=(25, 18, 30))
        hr = int(ir * 0.30)
        d.ellipse([x - ir // 2 - hr, ey - ir // 2 - hr, x - ir // 2 + hr, ey - ir // 2 + hr],
                  fill=(255, 255, 255))
        d.ellipse([x + ir // 3, ey + ir // 4, x + ir // 3 + hr, ey + ir // 4 + hr],
                  fill=(255, 255, 255, 180))
        # palpebra superiore marcata
        d.arc([x - ew, ey - eh, x + ew, ey + eh], 190, 350, fill=LINE, width=S * 3)
        # ciglia
        if c["gender"] in ("f", "c"):
            d.line([(x + sx * ew, ey - eh // 2), (x + sx * (ew + S * 5), ey - eh)], fill=LINE, width=S * 2)
    # sopracciglia
    by = ey - int(eh * 2.1)
    bw = int(ew * 1.1)
    for sx in (-1, 1):
        x = cx + sx * ex_off
        if c["mouth"] == "smirk":
            d.line([(x - bw, by + (0 if sx < 0 else -S * 4)), (x + bw, by + (-S * 4 if sx < 0 else 0))],
                   fill=lerp(c["hair_dark"], LINE, 0.4), width=S * 3)
        else:
            d.arc([x - bw, by - S * 6, x + bw, by + S * 8], 200, 340,
                  fill=lerp(c["hair_dark"], LINE, 0.4), width=S * 3)


def draw_nose_mouth(d, cx, cy, rw, rh, c):
    # naso a tratto
    ny = cy + int(rh * 0.42)
    d.line([(cx + S, ny - S * 4), (cx + S * 3, ny)], fill=lerp(LINE, c["skin"], 0.35), width=S * 2)
    # bocca
    my = cy + int(rh * 0.62)
    mw = int(rw * 0.30)
    style = c["mouth"]
    if style == "smirk":
        d.arc([cx - mw, my - S * 6, cx + mw, my + S * 8], 200, 335, fill=LINE, width=S * 3)
    elif style in ("smile", "grin"):
        d.arc([cx - mw, my - S * 8, cx + mw, my + S * 6], 15, 165, fill=LINE, width=S * 3)
    elif style == "big_smile":
        d.chord([cx - mw, my - S * 6, cx + mw, my + S * 12], 10, 170, fill=(210, 90, 90), outline=LINE, width=S * 2)
    elif style == "line":
        d.line([(cx - mw // 2, my), (cx + mw // 2, my)], fill=LINE, width=S * 2)
    else:  # soft / calm
        d.arc([cx - mw + S * 4, my - S * 5, cx + mw - S * 4, my + S * 5], 20, 160, fill=LINE, width=S * 2)


def strand(d, x0, y0, x1, y1, width, color):
    """Ciocca curva."""
    mx = (x0 + x1) / 2 + (y1 - y0) * 0.12
    my = (y0 + y1) / 2
    pts = []
    for t in range(13):
        u = t / 12
        x = (1 - u) ** 2 * x0 + 2 * (1 - u) * u * mx + u ** 2 * x1
        y = (1 - u) ** 2 * y0 + 2 * (1 - u) * u * my + u ** 2 * y1
        pts.append((x, y))
    d.line(pts, fill=color, width=width, joint="curve")


def draw_hair(d, cx, cy, rw, rh, c, rng):
    style = c["hair_style"]
    hc, hd = c["hair"], c["hair_dark"]
    shine = lerp(hc, (255, 255, 255), 0.35)
    top = cy - rh
    if style == "holo":
        # "capelli" olografici: corona di triangoli geometrici
        for i in range(9):
            a = math.pi * (0.12 + 0.76 * i / 8)
            x = cx - math.cos(a) * rw * 1.15
            y = cy - math.sin(a) * rh * 1.2
            d.polygon([(x, y), (x - rw * 0.12, y + rh * 0.3), (x + rw * 0.12, y + rh * 0.28)],
                      fill=hc if i % 2 else hd, outline=c["uniform2"], width=S)
        return
    # calotta base
    d.chord([cx - rw * 1.12, top - rh * 0.34, cx + rw * 1.12, cy + rh * 0.55], 180, 360, fill=hd)
    d.chord([cx - rw * 1.06, top - rh * 0.26, cx + rw * 1.06, cy + rh * 0.42], 180, 360, fill=hc)
    if style == "short_wavy":
        for i in range(11):
            a = math.pi * (0.06 + 0.88 * i / 10)
            x0 = cx - math.cos(a) * rw * 0.9
            y0 = top - rh * 0.05
            x1 = cx - math.cos(a) * rw * (1.1 + rng.uniform(0, 0.15))
            y1 = cy + rh * (0.1 + rng.uniform(0, 0.35))
            strand(d, x0, y0, x1, y1, int(rw * 0.16), hc if i % 2 else hd)
    elif style == "tied_back":
        d.ellipse([cx + rw * 0.75, cy - rh * 0.2, cx + rw * 1.25, cy + rh * 0.45], fill=hd, outline=LINE, width=S * 2)
        for i in range(7):
            a = math.pi * (0.15 + 0.7 * i / 6)
            x1 = cx - math.cos(a) * rw * 0.95
            strand(d, cx, top - rh * 0.15, x1, cy - rh * 0.35, int(rw * 0.14), hc if i % 2 else hd)
    elif style == "bun":
        d.ellipse([cx - rw * 0.35, top - rh * 0.75, cx + rw * 0.35, top - rh * 0.05],
                  fill=hc, outline=LINE, width=S * 2)
        d.arc([cx - rw * 0.28, top - rh * 0.65, cx + rw * 0.28, top - rh * 0.12], 0, 360, fill=hd, width=S * 2)
        for i in range(8):
            a = math.pi * (0.12 + 0.76 * i / 7)
            x1 = cx - math.cos(a) * rw * 1.0
            strand(d, cx, top - rh * 0.1, x1, cy - rh * 0.25, int(rw * 0.13), hc if i % 2 else hd)
    elif style == "bandana":
        d.chord([cx - rw * 1.08, top - rh * 0.3, cx + rw * 1.08, cy - rh * 0.1], 180, 360,
                fill=c["uniform2"], outline=LINE, width=S * 2)
        d.line([(cx - rw * 1.02, cy - rh * 0.55), (cx + rw * 1.02, cy - rh * 0.55)], fill=LINE, width=S * 2)
        knot = (cx + rw * 0.95, cy - rh * 0.75)
        d.polygon([knot, (knot[0] + rw * 0.28, knot[1] - rh * 0.1), (knot[0] + rw * 0.22, knot[1] + rh * 0.18)],
                  fill=c["uniform2"], outline=LINE, width=S * 2)
    elif style == "pigtails":
        for sx in (-1, 1):
            bx = cx + sx * rw * 1.15
            # treccina: 3 sfere in colonna
            for k in range(3):
                yy = cy - rh * 0.15 + k * rh * 0.34
                rr = rw * (0.2 - k * 0.03)
                d.ellipse([bx - rr, yy - rr, bx + rr, yy + rr],
                          fill=hc if k % 2 == 0 else hd, outline=LINE, width=S * 2)
            d.ellipse([bx - rw * 0.16, cy - rh * 0.42, bx + rw * 0.16, cy - rh * 0.1],
                      fill=c["uniform2"], outline=LINE, width=S)
        for i in range(9):
            a = math.pi * (0.1 + 0.8 * i / 8)
            x1 = cx - math.cos(a) * rw * 0.95
            strand(d, cx, top - rh * 0.12, x1, cy - rh * 0.3, int(rw * 0.13), hc if i % 2 else hd)
    elif style == "android":
        # casco liscio con placca centrale
        d.arc([cx - rw * 1.06, top - rh * 0.26, cx + rw * 1.06, cy + rh * 0.42], 180, 360, fill=LINE, width=S * 2)
        d.polygon([(cx - rw * 0.1, top - rh * 0.28), (cx + rw * 0.1, top - rh * 0.28),
                   (cx + rw * 0.06, cy - rh * 0.55), (cx - rw * 0.06, cy - rh * 0.55)],
                  fill=c["uniform2"], outline=LINE, width=S)
    # frangia sulla fronte (non per android/bandana)
    if style in ("short_wavy", "tied_back", "bun", "pigtails"):
        fy = cy - rh * 0.45
        n = 6
        for i in range(n):
            x0 = cx - rw * 0.85 + (2 * rw * 0.85) * i / (n - 1)
            d.polygon([(x0 - rw * 0.16, fy - rh * 0.3), (x0 + rw * 0.16, fy - rh * 0.3),
                       (x0 + rng.uniform(-0.06, 0.06) * rw, fy + rh * (0.12 + rng.uniform(0, 0.1)))],
                      fill=hc if i % 2 else hd)
        # lucido
        d.arc([cx - rw * 0.8, top - rh * 0.18, cx + rw * 0.8, cy], 210, 280, fill=shine, width=S * 4)
    elif style == "android":
        d.arc([cx - rw * 0.8, top - rh * 0.16, cx + rw * 0.8, cy], 210, 280, fill=shine, width=S * 4)


def draw_extras(d, cx, cy, rw, rh, c, rng):
    ex = c["extra"]
    ey = cy + int(rh * 0.12)
    ex_off = int(rw * 0.45)
    ew = int(rw * 0.30)
    if "glasses" in ex:
        gl = lerp(LINE, (200, 200, 220), 0.3)
        for sx in (-1, 1):
            x = cx + sx * ex_off
            d.rounded_rectangle([x - ew - S * 3, ey - int(rh * 0.22) - S * 2, x + ew + S * 3, ey + int(rh * 0.22)],
                                radius=S * 6, outline=gl, width=S * 2)
        d.line([(cx - ex_off + ew, ey - S * 4), (cx + ex_off - ew, ey - S * 4)], fill=gl, width=S * 2)
    if "freckles" in ex:
        fc = lerp(c["skin"], (90, 40, 20), 0.4)
        for _ in range(9):
            x = cx + rng.uniform(-0.75, 0.75) * rw
            y = cy + rh * 0.38 + rng.uniform(-0.06, 0.08) * rh
            if abs(x - cx) < rw * 0.2:
                continue
            d.ellipse([x - S, y - S, x + S, y + S], fill=fc)
    if "beard" in ex:
        bd = c["hair_dark"]
        d.polygon([(cx - rw * 0.72, cy + rh * 0.32), (cx + rw * 0.72, cy + rh * 0.32),
                   (cx + rw * 0.45, cy + rh * 1.15), (cx, cy + rh * 1.3),
                   (cx - rw * 0.45, cy + rh * 1.15)],
                  fill=bd, outline=LINE, width=S * 2)
        # bocca sopra la barba
        d.arc([cx - rw * 0.3, cy + rh * 0.5, cx + rw * 0.3, cy + rh * 0.75], 15, 165,
              fill=(200, 140, 130), width=S * 3)
    if "age" in ex:
        wr = lerp(c["skin"], LINE, 0.35)
        for sx in (-1, 1):
            x = cx + sx * ex_off
            d.arc([x - ew, ey + rh * 0.22, x + ew, ey + rh * 0.42], 200, 340, fill=wr, width=S)
    if "plates" in ex:
        pl = lerp(c["skin"], c["uniform2"], 0.5)
        d.line([(cx - rw * 0.98, cy), (cx - rw * 0.35, cy + rh * 0.1)], fill=pl, width=S * 2)
        d.line([(cx + rw * 0.98, cy), (cx + rw * 0.35, cy + rh * 0.1)], fill=pl, width=S * 2)
        d.line([(cx, cy + rh * 0.85), (cx, cy + rh * 1.0)], fill=pl, width=S * 2)
    if "flowers" in ex:
        for k in range(3):
            x = cx - rw * 1.5 + k * rw * 0.35
            y = cy + rh * 2.1 + (k % 2) * rh * 0.2
            for a in range(5):
                aa = 2 * math.pi * a / 5
                d.ellipse([x + math.cos(aa) * S * 6 - S * 4, y + math.sin(aa) * S * 6 - S * 4,
                           x + math.cos(aa) * S * 6 + S * 4, y + math.sin(aa) * S * 6 + S * 4],
                          fill=(160, 255, 220))
            d.ellipse([x - S * 3, y - S * 3, x + S * 3, y + S * 3], fill=(255, 250, 180))
    if "holo" in ex:
        # scanline olografiche su tutto il volto
        for y in range(int(cy - rh * 1.6), int(cy + rh * 2), S * 8):
            d.line([(cx - rw * 1.4, y), (cx + rw * 1.4, y)], fill=(120, 200, 255, 60), width=S)


def make_portrait(name):
    c = CHARS[name]
    rng = random.Random(hash(name) & 0xFFFF)
    w, h = W * S, H * S
    base = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(base, "RGBA")
    draw_background(d, w, h, c)
    glow_ring(base, c)
    d = ImageDraw.Draw(base, "RGBA")
    draw_bust(d, w, h, c)
    cx, cy, rw, rh = draw_face(d, w, h, c)
    draw_hair(d, cx, cy, rw, rh, c, rng)
    draw_eyes(d, cx, cy, rw, rh, c)
    if "beard" not in c["extra"]:
        draw_nose_mouth(d, cx, cy, rw, rh, c)
    else:
        ny = cy + int(rh * 0.42)
        d.line([(cx + S, ny - S * 4), (cx + S * 3, ny)], fill=lerp(LINE, c["skin"], 0.35), width=S * 2)
    draw_extras(d, cx, cy, rw, rh, c, rng)
    img = base.resize((W, H), Image.LANCZOS).convert("RGBA")
    PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)
    out = PORTRAITS_DIR / f"{name}.png"
    img.save(out)
    print(f"[pil] {out}")


def make_background(name):
    rng = random.Random(99 if name == "title" else 77)
    w, h = 1280, 720
    if name == "title":
        img = v_gradient((w, h), (8, 10, 30), (30, 12, 50)).convert("RGB")
        d = ImageDraw.Draw(img, "RGBA")
        # nebulosa: blob teal/viola sfocati
        neb = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        nd = ImageDraw.Draw(neb)
        for _ in range(26):
            x, y = rng.randint(0, w), rng.randint(0, h)
            r = rng.randint(60, 220)
            col = rng.choice([(40, 160, 160), (110, 60, 180), (60, 90, 200)])
            nd.ellipse([x - r, y - r, x + r, y + r], fill=col + (rng.randint(30, 80),))
        neb = neb.filter(ImageFilter.GaussianBlur(60))
        img.paste(neb, (0, 0), neb)
        d = ImageDraw.Draw(img, "RGBA")
    else:
        img = v_gradient((w, h), (10, 12, 40), (255, 170, 90)).convert("RGB")
        d = ImageDraw.Draw(img, "RGBA")
        # pianeta in basso
        pr = 900
        d.ellipse([w // 2 - pr, h - 260, w // 2 + pr, h - 260 + 2 * pr], fill=(50, 60, 110))
        d.ellipse([w // 2 - pr, h - 250, w // 2 + pr, h - 250 + 2 * pr], fill=(35, 45, 90))
        # alba: bagliore dorato sul bordo
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([w // 2 - 340, h - 330, w // 2 + 340, h - 40], fill=(255, 220, 140, 200))
        glow = glow.filter(ImageFilter.GaussianBlur(70))
        img.paste(glow, (0, 0), glow)
        d = ImageDraw.Draw(img, "RGBA")
        d.ellipse([w // 2 - 70, h - 300, w // 2 + 70, h - 160], fill=(255, 250, 220))
    # stelle
    for _ in range(340):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        b = rng.randint(120, 255)
        s = rng.choice([1, 1, 1, 2])
        d.ellipse([x, y, x + s, y + s], fill=(b, b, min(255, b + 20)))
    if name == "title":
        # silhouette nave-arca
        sx, sy = w // 2, int(h * 0.52)
        hull = (18, 22, 36)
        edge = (90, 220, 210)
        d.polygon([(sx - 340, sy), (sx - 180, sy - 46), (sx + 260, sy - 40),
                   (sx + 360, sy - 6), (sx + 300, sy + 40), (sx - 200, sy + 48)],
                  fill=hull, outline=edge, width=2)
        d.polygon([(sx - 60, sy - 46), (sx + 30, sy - 96), (sx + 120, sy - 42)], fill=hull, outline=edge, width=2)
        d.ellipse([sx - 320, sy - 90, sx - 240, sy - 40], fill=hull, outline=edge, width=2)  # anello
        for i in range(10):  # oblo' illuminati
            d.ellipse([sx - 150 + i * 40, sy - 8, sx - 144 + i * 40, sy - 2], fill=(255, 240, 170))
        # scia motori
        for i, a in ((0, 180), (10, 90), (26, 40)):
            d.polygon([(sx - 340 - i, sy - 6), (sx - 480 - i * 3, sy + 4), (sx - 340 - i, sy + 14)],
                      fill=(120, 230, 255, a))
    BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)
    out = BACKGROUNDS_DIR / f"{name}.png"
    img.save(out)
    print(f"[pil] {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    names = list(CHARS) + ["title", "ending"] if args.all else args.names
    if not names:
        ap.error("indicare nomi o --all")
    for n in names:
        if n in CHARS:
            make_portrait(n)
        elif n in ("title", "ending"):
            make_background(n)
        else:
            raise SystemExit(f"nome sconosciuto: {n}")


if __name__ == "__main__":
    main()
