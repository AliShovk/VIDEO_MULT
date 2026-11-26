"""Episode: «Что будет, если человек потеряет гравитацию на Земле?» — flat 2D."""
import json
import math
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in (ROOT, os.path.join(ROOT, "engine")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import settings as S  # noqa: E402
import flat2d as F  # noqa: E402
from flat2d import (INK, CREAM, CREAM_D, FLOOR, CORAL, MUSTARD, TEAL, TEAL_D, SKY, WHITE,
                    BLUE, SAND, GREEN, W, H, U, CW, CH, FPS, DUR, T, SCENES,
                    clamp, smooth, ease_out, ease_in, back_out, lerp, P, L, font)

SC_W, SC_H = 1500, 2500
GROUND = 1830.0
SW, SH = int(SC_W * U), int(SC_H * U)
CAP_Y = 1692
SPACE = (18, 24, 42)
SPACE_D = (32, 42, 66)
STAR = (238, 242, 250)


class Cam:
    def __init__(self, cx, cy, z):
        self.cx, self.cy, self.z = cx, cy, z

    def view(self):
        w, h = W / self.z, H / self.z
        return (clamp(self.cx - w / 2, 0, SC_W - w), clamp(self.cy - h / 2, 0, SC_H - h), w, h)


def shadow(d, x, y, w, a=46):
    d.ellipse([P(x - w, y - w * 0.22), P(x + w, y + w * 0.22)],
              fill=(INK[0], INK[1], INK[2], a))


# ------------------------------------------------------------------ backgrounds
def bg_room(d, t, dark=0.0):
    d.rectangle([0, 0, SW, SH], fill=CREAM)
    d.rectangle([0, 0, SW, int(980 * U)], fill=(250, 240, 224))
    # window with a flat sky
    wx0, wy0, wx1, wy1 = 980, 380, 1340, 760
    F.rrect(d, (wx0, wy0, wx1, wy1), 18, SKY, INK, 8)
    d.line([P((wx0 + wx1) / 2, wy0 + 8), P((wx0 + wx1) / 2, wy1 - 8)], fill=INK, width=L(6))
    d.line([P(wx0 + 8, (wy0 + wy1) / 2), P(wx1 - 8, (wy0 + wy1) / 2)], fill=INK, width=L(6))
    # floor
    d.rectangle([0, int(GROUND * U), SW, SH], fill=FLOOR)
    d.line([P(0, GROUND), P(SC_W, GROUND)], INK, 7)
    # wall lamp glow (flat)
    F.circle(d, (300, 470), 90, (252, 226, 176), None, 0)
    # wallpaper stripes
    for i in range(8):
        d.line([P(80 + i * 150, 60), P(80 + i * 150, GROUND - 40)], fill=(241, 226, 206), width=L(18))
    if dark > 0:
        d.rectangle([0, 0, SW, SH], fill=(10, 14, 26, int(150 * dark)))


def bg_space(d, t, stars=70, horizon=True):
    d.rectangle([0, 0, SW, SH], fill=SPACE)
    for i in range(stars):
        sx = (i * 197 + 60) % SC_W
        sy = (i * 263 + 40) % SC_H
        tw = 0.6 + 0.4 * math.sin(t * 2 + i)
        F.circle(d, (sx, sy), (3 + (i % 3) * 2) * tw, STAR, None, 0)
    # earth limb
    if horizon:
        d.ellipse([P(-500, GROUND - 300), P(SC_W + 500, GROUND + 1400)],
                  fill=(38, 92, 108), outline=None, width=0)
        d.arc([P(-500, GROUND - 300), P(SC_W + 500, GROUND + 1400)], 200, 340,
              fill=(120, 220, 230), width=L(8))


# ------------------------------------------------------------------ props
def mug(d, x, y, s=1.0, rot_=0.0):
    rrect_box = (x - 42 * s, y - 50 * s, x + 42 * s, y + 50 * s)
    F.rrect(d, rrect_box, 14 * s, CORAL, INK, 6)
    d.arc([P(x + 26 * s, y - 26 * s), P(x + 78 * s, y + 26 * s)], 300, 60, fill=INK, width=L(6))


def book(d, x, y, s=1.0, rot_=0.0):
    F.rrect(d, (x - 60 * s, y - 22 * s, x + 60 * s, y + 22 * s), 6, MUSTARD, INK, 6)
    d.line([P(x - 30 * s, y - 18 * s), P(x - 30 * s, y + 18 * s)], fill=INK, width=L(5))
    d.line([P(x - 10 * s, y - 8 * s), P(x + 44 * s, y - 8 * s)], fill=(240, 220, 190), width=L(5))


def pencil(d, x, y, s=1.0):
    F.rrect(d, (x - 8 * s, y - 60 * s, x + 8 * s, y + 40 * s), 4, (244, 196, 92), INK, 5)
    F.poly(d, [(x - 8 * s, y + 40 * s), (x + 8 * s, y + 40 * s), (x, y + 66 * s)], (60, 44, 40), INK, 5)


def toggle(d, x, y, on=True, s=1.0):
    F.rrect(d, (x - 90 * s, y - 46 * s, x + 90 * s, y + 46 * s), 40 * s, (228, 226, 220), INK, 7)
    cx = x + (40 if on else -40) * s
    F.circle(d, (cx, y), 34 * s, TEAL if on else CORAL, INK, 7)
    d.text(P(x, y + 74 * s), "ГРАВИТАЦИЯ", font=font(30), fill=INK, anchor="mm")
    d.text(P(x, y + 108 * s), "ВКЛ" if on else "ВЫКЛ", font=font(34), fill=(TEAL_D if on else CORAL), anchor="mm")


def speed_badge(d, x, y, v, s=1.0):
    F.plate(d, (x - 190 * s, y - 66 * s, x + 190 * s, y + 66 * s), r=26, fill=CORAL, bw=6)
    d.text(P(x, y - 10 * s), f"{int(v)}", font=font(62), fill=WHITE, anchor="mm")
    d.text(P(x, y + 40 * s), "КМ/Ч", font=font(26), fill=WHITE, anchor="mm")


def crack(d, t, grow=1.0):
    pts = [(700, GROUND + 10)]
    for i in range(9):
        pts.append((700 + (i % 2) * 70 - 35, GROUND - 40 - i * 130 * grow))
    d.polygon([P(*p) for p in pts] + [P(830, GROUND + 10)], fill=(46, 34, 30))
    for (px, py) in pts[1:]:
        d.line([P(px, py), P(px + 90, py + 40)], fill=INK, width=L(6))


# ------------------------------------------------------------------ scenes
def scene0(d, t):
    """Hook: the switch flips, the room lets go."""
    a, b = SCENES[0]
    p = clamp((t - a) / max(0.001, b - a))
    off = p > 0.42
    bg_room(d, t, dark=0.0 if not off else clamp((p - 0.42) * 2.2) * 0.55)
    x = 640.0
    h = 340.0
    float_y = 0.0
    if off:
        fu = clamp((p - 0.42) / 0.45)
        float_y = -150 * ease_out(fu)
    # toggle on the wall
    toggle(d, 300, 620, on=not off, s=1.0)
    # floating props
    if off:
        fu = clamp((p - 0.42) / 0.5)
        mug(d, 980 - 20 * fu, 1180 - 260 * fu, 0.9)
        book(d, 1150 + 30 * fu, 1320 - 200 * fu, 0.8)
        pencil(d, 850 - 40 * fu, 1280 - 320 * fu, 0.9)
    sh_a = int(46 * (1 - clamp((p - 0.42) * 2.4)))
    if sh_a > 4:
        shadow(d, x, GROUND, 90, a=sh_a)
    pose = dict(front_leg=(-24, 34) if off else (-8, 10), back_leg=(18, 28) if off else (8, 8),
                front_arm=(-46, 24) if off else (-16, 10), back_arm=(38, 20) if off else (16, 12),
                head=2 * math.sin(t * 2), lean=-6 if off else 0,
                mouth="o" if off else "flat", brow=8 if off else 0)
    if 0.12 < p < 0.42:
        pose["front_arm"] = (-150, -10)
    F.hero(d, x, GROUND + float_y, h, pose)
    # dust motes rising
    if off:
        for i in range(8):
            ph = ((t - a) * 0.5 + i * 0.13) % 1.0
            F.circle(d, (300 + i * 120, GROUND - ph * 600), 5 + (i % 3) * 3, (255, 250, 240, 200), None, 0)


def scene1(d, t):
    """Eastward fling: everything slides sideways at 1600 km/h."""
    a, b = SCENES[1]
    p = clamp((t - a) / max(0.001, b - a))
    d.rectangle([0, 0, SW, SH], fill=(250, 240, 224))
    d.rectangle([0, 0, SW, int(900 * U)], fill=SKY)
    d.rectangle([0, int(GROUND * U), SW, SH], fill=FLOOR)
    d.line([P(0, GROUND), P(SC_W, GROUND)], INK, 7)
    scroll = (t - a) * 2600
    for i in range(16):
        gx = (i * 180 - scroll) % (SC_W + 240) - 120
        d.line([P(gx, GROUND + 40), P(gx + 90, GROUND + 40)], fill=(198, 172, 138), width=L(7))
    for i in range(10):
        sx = (i * 260 - scroll * 1.6) % (SC_W + 300) - 150
        d.line([P(sx, 620 + (i % 3) * 120), P(sx + 200, 620 + (i % 3) * 120)],
               fill=(255, 255, 255, 150), width=L(6))
    # the pole he hangs onto
    F.rrect(d, (760, 420, 830, GROUND), 12, (206, 198, 186), INK, 7)
    x, h = 700.0, 330.0
    lean = -22
    pose = dict(front_leg=(-26, 34), back_leg=(-6, 26), front_arm=(-120, -30), back_arm=(-96, -40),
                lean=lean, head=-8, mouth="o", brow=9)
    F.hero(d, x, GROUND - 260, h, pose)
    # speed lines behind the hero
    for i in range(6):
        yy = 900 + i * 90
        d.line([P(60, yy), P(520, yy)], fill=(*CORAL, 170), width=L(7))
    speed_badge(d, 300, 420, 1600 * clamp((t - a) / 1.2), 1.0)


def scene2(d, t):
    """Air leaves: sky turns to space, the streams go up."""
    a, b = SCENES[2]
    p = clamp((t - a) / max(0.001, b - a))
    bg_space(d, t, stars=60, horizon=True)
    for i in range(14):
        sx = 40 + i * 108
        ph = ((t - a) * 0.85 + i * 0.07) % 1.0
        y0 = GROUND - 40 - ph * 1200
        wob = 26 * math.sin(ph * 7 + i * 0.8)
        d.line([P(sx, y0 + 190), P(sx + wob, y0 + 90), P(sx + wob * 0.6, y0)],
               fill=(214, 238, 252, 200), width=L(7))
        F.circle(d, (sx + wob * 0.6, y0 - 12), 8, (238, 250, 255), None, 0)
    # thin haze leaving the horizon
    for k in range(3):
        d.arc([P(-200, GROUND - 260 - k * 60), P(SC_W + 200, GROUND + 140 - k * 40)], 200, 340,
              fill=(210, 234, 248, 90), width=L(16))
    x, h = 620.0, 330.0
    hover = 40 * math.sin(2 * math.pi * (t - a) / 3.0)
    pose = dict(front_leg=(-18, 24), back_leg=(12, 18),
                front_arm=(-34, 96), back_arm=(30, 92),
                head=6 * math.sin(t * 3), mouth="o", brow=10)
    F.hero(d, x, GROUND - 120 + hover, h, pose)
    # throat clutch marks
    for i in range(2):
        d.arc([P(x - 40 - i * 16, GROUND - 360), P(x + 40 + i * 16, GROUND - 250)],
              200, 340, fill=CORAL, width=L(6))
    d.text(P(300, 470), "0%", font=font(96), fill=CORAL, anchor="mm")
    d.text(P(300, 540), "ВОЗДУХА", font=font(30), fill=WHITE, anchor="mm")


def scene3(d, t):
    """Blood goes up: puffy face, pressure."""
    a, b = SCENES[3]
    p = clamp((t - a) / max(0.001, b - a))
    d.rectangle([0, 0, SW, SH], fill=(248, 236, 228))
    for i in range(6):
        d.line([P(0, 200 + i * 320), P(SC_W, 140 + i * 320)], fill=(240, 222, 214), width=L(26))
    x, h = 760.0, 520.0
    pose = dict(front_leg=(-10, 14), back_leg=(10, 12), front_arm=(-40, 70), back_arm=(36, 66),
                head=-4, mouth="flat", brow=8, eyes="open")
    F.hero(d, x, GROUND, h, pose)
    # red cheeks and nose drawn on top of the face
    hx, hy = x, GROUND - h * 0.84
    kk = h / 300.0
    for cxs in (-1, 1):
        F.circle(d, (hx + cxs * 26 * kk, hy + 14 * kk), 17 * kk, (230, 110, 100, 210), None, 0)
    F.circle(d, (hx, hy + 2 * kk), 9 * kk, (226, 96, 92, 220), None, 0)
    # rising droplets (fluid shift) with motion trails
    for i in range(7):
        ph = ((t - a) * 0.7 + i * 0.14) % 1.0
        dx = hx - 130 + i * 44
        dy = hy + 60 - ph * 260
        d.line([P(dx + 10 * math.sin(ph * 8 + i), dy + 34), P(dx + 10 * math.sin(ph * 8 + i), dy + 12)],
               fill=(*CORAL, 120), width=L(6))
        F.circle(d, (dx + 10 * math.sin(ph * 8 + i), dy), 12, (200, 90, 96), INK, 4)
    # arrow + pressure badge
    ay = hy - 190
    d.line([P(hx + 150, ay + 90), P(hx + 150, ay - 40)], fill=CORAL, width=L(10))
    d.line([P(hx + 130, ay - 16), P(hx + 150, ay - 44), P(hx + 170, ay - 16)], fill=CORAL, width=L(10))
    # heartbeat
    bx, by = 300, 700
    beat = 1 + 0.18 * math.sin(2 * math.pi * (t - a) * 2.0) ** 8
    F.circle(d, (bx, by), 54 * beat, CORAL, INK, 7)
    d.text(P(bx, by), "♥", font=font(52), fill=WHITE, anchor="mm")


def scene4(d, t):
    """Inner ear loses up."""
    a, b = SCENES[4]
    p = clamp((t - a) / max(0.001, b - a))
    d.rectangle([0, 0, SW, SH], fill=(28, 34, 50))
    for i in range(55):
        sx = (i * 211 + 40) % SC_W
        sy = (i * 173 + 30) % SC_H
        F.circle(d, (sx, sy), 3 + (i % 3) * 2, (150, 170, 200), None, 0)
    # spiral
    cx, cy = 900, 900
    for k in range(3):
        r = 120 + k * 90
        d.arc([P(cx - r, cy - r), P(cx + r, cy + r)], 0 + k * 40, 300 + k * 20,
              fill=(*MUSTARD, 150), width=L(7))
    x, h = 600.0, 340.0
    tilt = 14 * math.sin(2 * math.pi * (t - a) / 2.2)
    pose = dict(front_leg=(-22, 30), back_leg=(18, 24), front_arm=(-120, -20), back_arm=(110, -24),
                lean=tilt, head=tilt * 1.4, mouth="o", brow=9)
    F.hero(d, x, GROUND - 300 + 20 * math.sin(t * 2), h, pose)
    # two conflicting "up" arrows
    d.line([P(400, 1450), P(330, 1120)], fill=CORAL, width=L(10))
    d.line([P(310, 1150), P(330, 1112), P(360, 1146)], fill=CORAL, width=L(10))
    d.line([P(560, 1120), P(700, 1430)], fill=TEAL, width=L(10))
    d.line([P(676, 1400), P(704, 1434), P(666, 1446)], fill=TEAL, width=L(10))
    d.text(P(330, 1080), "ГЛАЗА", font=font(28), fill=CORAL, anchor="mm")
    d.text(P(740, 1460), "УХО", font=font(28), fill=TEAL, anchor="mm")


def scene5(d, t):
    """The planet splits: core pressure with nothing holding it."""
    a, b = SCENES[5]
    p = clamp((t - a) / max(0.001, b - a))
    bg_space(d, t, stars=80, horizon=False)
    cx, cy, r = 750, GROUND + 640, 980
    split = ease_out(clamp((p - 0.12) / 0.7))
    dx = 150 * split
    dy = 40 * split
    rot = 5 * split

    def wedge(a0, a1, ox, oy, ang, jag=0):
        pts = []
        for k in range(a1 - a0 + 1):
            th = math.radians(a0 + k)
            rr = r + (jag if (k % 2 == 0) else -jag)
            pts.append((cx + rr * math.cos(th) + ox, cy + rr * math.sin(th) + oy))
        return pts

    # two crust halves drifting apart
    for (a0, a1, sgn) in ((186, 268, -1), (272, 354, 1)):
        pts = wedge(a0, a1, sgn * dx, dy, rot, jag=46)
        F.poly(d, pts + [(cx + sgn * 70 + sgn * dx, cy - r * 0.5 + dy)],
               (74, 128, 96), INK, 7)
        # crust on the inner edge
        inner = pts[:1] + [(cx + sgn * 70 + sgn * dx, cy - r * 0.5 + dy)] + pts[-1:]
        F.poly(d, inner, (96, 74, 62), INK, 5)
    # glowing core between the halves
    cr = 120 * (0.6 + 0.4 * split)
    for k in range(3):
        d.ellipse([P(cx - cr - k * 34, cy - r * 0.52 - cr - k * 30),
                   P(cx + cr + k * 34, cy - r * 0.52 + cr + k * 30)],
                  outline=(*MUSTARD, 90 - k * 25), width=L(8))
    F.circle(d, (cx, cy - r * 0.52), cr, (250, 190, 90), INK, 7)
    F.circle(d, (cx, cy - r * 0.52), cr * 0.55, (255, 238, 186), None, 0)
    # sparks out of the fissure
    for i in range(9):
        ph = ((t - a) * 0.9 + i * 0.11) % 1.0
        sx = cx - 60 + (i % 5) * 30
        sy = cy - r * 0.52 - ph * 520
        F.circle(d, (sx + 18 * math.sin(ph * 9 + i), sy), 5 + (i % 3) * 3, MUSTARD, None, 0)
    # rock chunks flying out
    for i in range(7):
        off = ease_out(clamp((p - 0.2 - i * 0.04) / 0.6))
        px = cx - 420 + i * 140
        py = GROUND - 40 - off * (260 + i * 30)
        F.poly(d, [(px, py), (px + 70, py - 40), (px + 120, py + 30), (px + 30, py + 60)],
               (96, 88, 80), INK, 5)
    # the hero tumbles above it
    x, h = 700.0, 300.0
    pose = dict(front_leg=(-26, 40), back_leg=(20, 34), front_arm=(-140, -26), back_arm=(130, -20),
                lean=16 * math.sin(2 * math.pi * (t - a) / 2.4), head=-8,
                mouth="o", brow=10)
    F.hero(d, x, GROUND - 300 + 26 * math.sin(t * 2), h, pose)
    d.text(P(300, 420), "3,6 МБАР", font=font(46), fill=MUSTARD, anchor="mm")
    d.text(P(300, 482), "ДАВЛЕНИЕ ЯДРА", font=font(24), fill=WHITE, anchor="mm")


def scene6(d, t):
    """Punchline: gravity holds everything."""
    a, b = SCENES[6]
    p = clamp((t - a) / max(0.001, b - a))
    bg_space(d, t, stars=90, horizon=False)
    x, h = 640.0, 380.0
    hover = 24 * math.sin(2 * math.pi * (t - a) / 3.4)
    # a large chunk of Earth under his feet
    F.ellipse(d, (x, GROUND + 150), 620, 300, (74, 128, 96), INK, 8)
    F.ellipse(d, (x, GROUND + 230), 600, 260, (96, 74, 62), None, 0)
    d.arc([P(x - 620, GROUND - 150), P(x + 620, GROUND + 450)], 200, 340, fill=INK, width=L(8))
    # two anchors on the crust: a tree and a stone
    F.poly(d, [(x - 430, GROUND - 6), (x - 360, GROUND - 150), (x - 300, GROUND - 6)], (48, 104, 72), INK, 6)
    d.rectangle([P(x - 340, GROUND - 30), P(x - 320, GROUND + 30)], fill=(92, 66, 48))
    F.ellipse(d, (x + 430, GROUND + 10), 70, 44, (120, 112, 104), INK, 6)

    # objects fall along lines pointing at the planet centre
    target = (x, GROUND + 150)
    for i, (px, py, s_) in enumerate(((x - 330, GROUND - 640, 0.9), (x + 360, GROUND - 720, 0.8))):
        drop = ease_in(clamp((p - 0.15 - i * 0.1) / 0.7))
        tx, ty = target
        ux, uy = tx - px, ty - py
        dist = math.hypot(ux, uy)
        ux, uy = ux / dist, uy / dist
        # land on the surface, not in the core
        land_pt = (px + ux * (dist - 470), py + uy * (dist - 470))
        cxp = lerp(px, land_pt[0], drop)
        cyp = lerp(py, land_pt[1], drop)
        if i == 0:
            mug(d, cxp, cyp, s_)
        else:
            book(d, cxp, cyp, s_)
        if drop < 0.95:
            a0x, a0y = cxp - ux * 90, cyp - uy * 90
            d.line([P(a0x, a0y), P(cxp - ux * 42, cyp - uy * 42)], fill=CORAL, width=L(7))
            px1, py1 = cxp - ux * 60, cyp - uy * 60
            d.line([P(px1 - uy * 16 + ux * 12, py1 + ux * 16 + uy * 12),
                    P(cxp - ux * 42, cyp - uy * 42),
                    P(px1 + uy * 16 + ux * 12, py1 - ux * 16 + uy * 12)], fill=CORAL, width=L(7))
    pose = dict(front_leg=(-10, 12), back_leg=(10, 10), front_arm=(-140, -10), back_arm=(140, -14),
                head=3 * math.sin(t * 2), mouth="smile", brow=0)
    F.hero(d, x, GROUND - 40 + hover, h, pose)


SCENE_FN = [scene0, scene1, scene2, scene3, scene4, scene5, scene6]
CAMS = [Cam(740, 1250, 1.02), Cam(700, 1300, 1.04), Cam(600, 1250, 1.06),
        Cam(760, 1400, 1.12), Cam(640, 1300, 1.05), Cam(700, 1320, 1.00),
        Cam(620, 1250, 1.02)]


# ------------------------------------------------------------------ UI
CAPS = [
    (1, "Сносит на восток: 1600 км/ч"),
    (2, "Воздух утекает в космос"),
    (3, "Кровь — в голову"),
    (4, "Верх и низ потеряны"),
    (5, "Планета разлетается"),
    (6, "Гравитация держит всё"),
]
STICK = {
    3: ("ДАВЛЕНИЕ", 0.40, CORAL),
    4: ("ГДЕ ВЕРХ?", 0.40, MUSTARD),
}


def ui_layer(t):
    lay = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a0, b0 = SCENES[0]
    if a0 <= t <= b0 + 0.12:
        p = clamp((t - a0) / max(0.001, b0 - a0))
        if p > 0.44:
            aa = int(255 * clamp((p - 0.44) / 0.12))
            d.text(P(W / 2, 300), "ГРАВИТАЦИЯ", font=font(74), fill=(*INK, aa), anchor="mm")
            d.text(P(W / 2, 390), "ВЫКЛЮЧИЛАСЬ", font=font(74), fill=(*CORAL, aa), anchor="mm")
    for i, text in CAPS:
        a = SCENES[i][0] + 0.02
        end = min(SCENES[i][1], a + (T[i]["end"] - T[i]["start"]) + 0.45)
        cap = F.caption(d, t, a, end, text, y=CAP_Y, w=900)
        if cap is not None:
            lay.alpha_composite(cap)
    for i, (txt, frac, col) in STICK.items():
        a = SCENES[i][0] + frac * (SCENES[i][1] - SCENES[i][0])
        if a <= t <= SCENES[i][1] + 0.05:
            u = back_out((t - a) / 0.26)
            im = F.sticker(txt, 44, col, rot_=-4 if i % 2 else 3)
            if u < 1:
                im = im.resize((max(2, int(im.width * u)), max(2, int(im.height * u))), Image.LANCZOS)
            lay.alpha_composite(im, (int(CW * 0.5 - im.width / 2), int(250 * U)))
    ec = T[6]["end"] + 0.15
    if t >= ec:
        a = ease_out((t - ec) / 0.4)
        box = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.rectangle([0, 0, CW, CH], fill=(INK[0], INK[1], INK[2], int(110 * a)))
        F.plate(bd, (80, 610, W - 80, 1000), r=44, fill=(255, 249, 238), bw=7, shadow=12)
        bd.text(P(W / 2, 696), "ПОДПИШИСЬ", font=font(78), fill=CORAL, anchor="mm")
        bd.text(P(W / 2, 788), "новые «что если» каждую неделю", font=font(36), fill=INK, anchor="mm")
        bd.text(P(W / 2, 878), "СОХРАНИ, ЧТОБЫ НЕ ПОТЕРЯТЬ", font=font(30), fill=TEAL_D, anchor="mm")
        if a < 1:
            box.putalpha(box.split()[3].point(lambda v: int(v * a)))
        lay.alpha_composite(box)
    return lay


# ------------------------------------------------------------------ frame
def compose(t):
    scene = Image.new("RGB", (SW, SH), CREAM)
    d = ImageDraw.Draw(scene, "RGBA")
    idx = len(SCENES) - 1
    for i, (a, b) in enumerate(SCENES):
        if a <= t < b:
            idx = i
    SCENE_FN[idx](d, t)

    a, b = SCENES[idx]
    p = clamp((t - a) / max(0.001, b - a))
    base = CAMS[idx]
    shake = 0
    if idx == 1:
        shake = 6
    if idx == 5:
        shake = 5 * clamp((p - 0.25) * 2)
    cam = Cam(base.cx + 10 * math.sin(2 * math.pi * t / 9.0) + shake * math.sin(t * 47),
              base.cy - 18 * p + shake * math.cos(t * 39), base.z * (1 + 0.035 * p))
    x0, y0, vw, vh = cam.view()
    crop = scene.crop((int(x0 * U), int(y0 * U), int((x0 + vw) * U), int((y0 + vh) * U)))
    frame = crop.resize((CW, CH), Image.LANCZOS).convert("RGBA")
    frame.alpha_composite(ui_layer(t))
    out = frame.convert("RGB").resize((W, H), Image.LANCZOS)
    return F.grain(out, seed=(int(t * 6) % 4), amount=0.30)


def frame_at(t):
    return compose(t)


def _work(i):
    return i, frame_at(i / FPS).tobytes()


def render_all(workers=3):
    frames_dir = S.get("paths.frames_dir", "frames")
    os.makedirs(frames_dir, exist_ok=True)
    n = int(round(DUR * FPS))
    done = {int(f[1:5]) for f in os.listdir(frames_dir) if f.startswith("f")}
    todo = [i for i in range(n) if i not in done]
    print(f"frames {len(done)}/{n}, todo {len(todo)}, DUR={DUR:.2f}", flush=True)
    if not todo:
        return
    from multiprocessing import Pool
    with Pool(workers) as pool:
        for k, (i, buf) in enumerate(pool.imap_unordered(_work, todo, chunksize=4)):
            Image.frombytes("RGB", (W, H), buf).save(os.path.join(frames_dir, f"f{i:04d}.png"))
            if k % 60 == 0:
                print(f"{k}/{len(todo)}", flush=True)
    print("frames done", flush=True)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        os.makedirs("preview", exist_ok=True)
        ts = [1.0, 2.2, 3.9, 5.6, 8.4, 10.4, 12.6, 15.2, 17.4, 20.2, 22.6, 25.4]
        sheet = Image.new("RGB", (300 * 4, 533 * 3), (24, 24, 26))
        for i, t in enumerate(ts):
            im = frame_at(t).resize((300, 533), Image.LANCZOS)
            sheet.paste(im, ((i % 4) * 300, (i // 4) * 533))
        sheet.save("preview/sheet.png")
        for t in (2.4, 5.4, 9.6, 12.8, 17.6, 21.0, 25.8):
            frame_at(t).resize((540, 960), Image.LANCZOS).save(f"preview/full_{t}.png")
        print("preview ok")
    elif "--render" in sys.argv:
        workers = int(S.get("video.workers", 3))
        if "--workers" in sys.argv:
            workers = int(sys.argv[sys.argv.index("--workers") + 1])
        render_all(workers)
