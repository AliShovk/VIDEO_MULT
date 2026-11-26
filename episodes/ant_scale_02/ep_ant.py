"""Episode: «Что, если ты станешь размером с муравья?» — flat 2D cartoon."""
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
HIP_Y_G = -200.0
SKIN_S = (243, 202, 162)


class Cam:
    def __init__(self, cx, cy, z):
        self.cx, self.cy, self.z = cx, cy, z

    def view(self):
        w, h = W / self.z, H / self.z
        x0 = clamp(self.cx - w / 2, 0, SC_W - w)
        y0 = clamp(self.cy - h / 2, 0, SC_H - h)
        return x0, y0, w, h


# ------------------------------------------------------------------ background
def bg_stage(d, t, kind="yard"):
    d.rectangle([0, 0, SW, SH], fill=CREAM)
    sky_top = {"yard": (250, 240, 224), "water": (238, 240, 232), "cold": (208, 232, 242),
               "table": (250, 240, 224), "sand": (250, 234, 206)}[kind]
    d.rectangle([0, 0, SW, int(980 * U)], fill=sky_top)

    if kind != "table":
        sx, sy = 1230, 330
        sun_col = (250, 214, 132) if kind != "cold" else (232, 244, 250)
        F.circle(d, (sx, sy), 112, sun_col, None, 0)
        for i in range(8):
            a = math.radians(i * 45)
            d.line([P(sx + 145 * math.cos(a), sy + 145 * math.sin(a)),
                    P(sx + 198 * math.cos(a), sy + 198 * math.sin(a))], sun_col, L(10))
        for (cx, cy, s) in ((250, 305, 1.0), (520, 205, 0.7)):
            cloud = (255, 252, 244) if kind != "cold" else (238, 248, 252)
            F.ellipse(d, (cx, cy), 108 * s, 50 * s, cloud, INK, 5)
            F.ellipse(d, (cx + 76 * s, cy - 16), 62 * s, 40 * s, cloud, INK, 5)

    d.rectangle([0, int(GROUND * U), SW, SH], fill=FLOOR if kind != "sand" else SAND)
    d.line([P(0, GROUND), P(SC_W, GROUND)], INK, 7)

    if kind in ("yard", "water"):
        for i, (bx, hh, lean, col) in enumerate([(150, 1050, -16, (44, 104, 78)),
                                                 (300, 780, 12, (58, 122, 92)),
                                                 (1330, 1120, 14, (44, 104, 78)),
                                                 (1190, 820, -12, (58, 122, 92))]):
            sway = 16 * math.sin(2 * math.pi * t / 5.0 + i)
            pts = [(bx - 30, GROUND + 10)]
            for k in range(1, 7):
                pts.append((bx + lean * k + sway * (k / 6) ** 2, GROUND - hh * k / 6))
            for k in range(6, 0, -1):
                pts.append((bx + 30 + lean * k * 0.8 + sway * (k / 6) ** 2, GROUND - hh * k / 6))
            F.poly(d, pts, col, INK, 6)
        for (px, py, pr) in [(430, GROUND - 8, 56), (1010, GROUND - 2, 40), (790, GROUND + 4, 26)]:
            F.ellipse(d, (px, py), pr, pr * 0.55, (214, 193, 164), INK, 6)
    elif kind == "cold":
        for i in range(24):
            yy = (i * 191 + t * 55) % (GROUND - 100)
            xx = (i * 233 + math.sin(t * 0.7 + i) * 60) % SC_W
            F.circle(d, (xx, yy), 12 + (i % 3) * 5, (250, 254, 255), None, 0)
        F.ice_cube(d, 980, GROUND - 175, 380)
        F.ice_cube(d, 250, GROUND - 120, 230)
        F.ice_cube(d, 1310, GROUND - 80, 150)
    elif kind == "table":
        d.rectangle([0, 0, SW, int(730 * U)], fill=(250, 240, 224))
        d.rectangle([0, int(670 * U), SW, int(742 * U)], fill=(198, 152, 108))
        d.line([P(0, 670), P(SC_W, 670)], INK, 7)
        d.line([P(0, 742), P(SC_W, 742)], INK, 7)
        d.rectangle([int(120 * U), int(742 * U), int(190 * U), SH], fill=(168, 124, 86))
        d.line([P(120, 742), P(120, SC_H)], INK, 6)
        d.line([P(190, 742), P(190, SC_H)], INK, 6)
    elif kind == "sand":
        for i in range(26):
            xx = (i * 187 + 60) % SC_W
            yy = GROUND + 34 + (i * 41) % 280
            F.circle(d, (xx, yy), 10 + (i % 4) * 5, (206, 172, 118), None, 0)
        for i in range(5):
            d.line([P(240 + i * 240, GROUND + 46), P(300 + i * 240, GROUND + 46)], (198, 160, 110), 6)


def shadow(d, x, y, w, a=46):
    d.ellipse([P(x - w, y - w * 0.22), P(x + w, y + w * 0.22)],
              fill=(INK[0], INK[1], INK[2], a))


# ------------------------------------------------------------------ scene 0: hook + shrink
def scene0(d, t):
    bg_stage(d, t, "yard")
    a, b = SCENES[0]
    p = clamp((t - a) / max(0.001, b - a))
    marks = [(0.06, 560), (0.30, 380), (0.52, 240), (0.74, 135)]
    h = 560.0
    for i, (pm, hv) in enumerate(marks):
        if p >= pm:
            nxt = marks[i + 1][0] if i + 1 < len(marks) else 1.0
            u = clamp((p - pm) / max(0.02, nxt - pm))
            h = lerp(hv, marks[i + 1][1] if i + 1 < len(marks) else 135, smooth(u))
    x = 720
    shadow(d, x, GROUND, 60 + h * 0.32)
    sway = 4 * math.sin(2 * math.pi * t / 3.0)
    pose = dict(front_arm=(-20 + sway, 12), back_arm=(18 - sway, 14),
                front_leg=(-6, 5), back_leg=(6, 5), head=2 * math.sin(t * 2),
                mouth="o" if 0.2 < p < 0.85 else "smile", brow=4 if p > 0.2 else 0)
    F.hero(d, x, GROUND, h, pose)
    for i, (pm, _) in enumerate(marks[1:]):
        u = clamp((p - pm) / 0.32)
        if 0 < u < 1:
            r = 30 + (300 - i * 60) * ease_out(u)
            d.ellipse([P(x - r, GROUND - h * 0.6 - r * 0.8), P(x + r, GROUND - h * 0.6 + r * 0.8)],
                      outline=(*CORAL, int(210 * (1 - u))), width=L(8))


# ------------------------------------------------------------------ scene 1: strength
def scene1(d, t):
    bg_stage(d, t, "yard")
    a, b = SCENES[1]
    p = clamp((t - a) / max(0.001, b - a))
    x, h = 470.0, 300.0
    lift = ease_out((p - 0.30) / 0.42)
    crouch = math.sin(clamp((p - 0.10) / 0.20) * math.pi)
    hh = h * (1 - 0.14 * crouch) * (1 + 0.03 * lift)
    shadow(d, x, GROUND, 78)
    pose = dict(
        front_leg=(-14 - 16 * crouch, 16 + 20 * crouch),
        back_leg=(16 + 14 * crouch, 14 + 16 * crouch),
        front_arm=(lerp(-18, -158, lift), lerp(12, -16, lift)),
        back_arm=(lerp(18, 158, lift), lerp(12, -16, lift)),
        lean=-2 - 7 * lift,
        mouth="o" if lift > 0.15 else "flat",
        brow=6 if lift > 0.1 else 0,
        squash=1 - 0.05 * crouch,
    )
    cs = 320.0
    if lift < 0.02:
        F.crumb(d, x + 150, GROUND - cs * 0.34, cs, rot_=-5)
        F.hero(d, x, GROUND, hh, pose)
    else:
        joints = F.hero(d, x, GROUND, hh, pose)
        hands = joints["hands"]
        hy = min(hands[0][1], hands[1][1])
        wob = 3.0 * math.sin(t * 26) * lift
        crumb_cy = hy - cs * 0.34 + wob
        F.crumb(d, x + 10, crumb_cy, cs, rot_=-5 + 5 * math.sin(t * 3))
        # re-draw palms on top of the crumb so the grip is visible
        for (hxp, hyp) in hands:
            F.circle(d, (hxp, hyp), 13 * (hh / 300.0) * 1.0, SKIN_S, INK, 5)
        # ground cracks under the load
        if lift > 0.5:
            aa = int(200 * clamp((lift - 0.5) / 0.3))
            for i in range(3):
                cx0 = x - 80 + i * 62
                d.line([P(cx0, GROUND + 6), P(cx0 - 24, GROUND + 34)], (*INK, aa), 5)
        if lift > 0.25:
            for i in range(3):
                r0 = 30 + i * 26
                d.arc([P(x + 10 - r0 - 60, crumb_cy - cs * 0.5 - r0), P(x + 10 + r0 + 40, crumb_cy + 30)],
                      205, 335, fill=(*CORAL, 190), width=L(7))
            F.circle(d, (x + 92, GROUND - hh - 26), 11, BLUE, INK, 4)
            F.circle(d, (x - 96, GROUND - hh - 8), 8, BLUE, INK, 3)
        if lift > 0.6:
            aa = int(255 * clamp((lift - 0.6) / 0.3))
            d.text(P(x + 10, crumb_cy - cs * 0.5 - 110), "×50", font=font(112), fill=(*CORAL, aa),
                   anchor="mm", stroke_width=L(5), stroke_fill=(*WHITE, aa))
    if p < 0.12:
        s = p / 0.12
        for i in range(5):
            ang = math.radians(200 + i * 28)
            r = 30 + 70 * s
            F.circle(d, (x + 150 + math.cos(ang) * r, GROUND - 10 + math.sin(ang) * r * 0.3),
                     14 * (1 - s) + 3, (222, 200, 168), None, 0)


# ------------------------------------------------------------------ scene 2: water
def scene2(d, t):
    bg_stage(d, t, "water")
    a, b = SCENES[2]
    p = clamp((t - a) / max(0.001, b - a))
    x, h = 505.0, 300.0
    bx = 890.0
    push = ease_out((p - 0.18) / 0.35)
    wobble = 7 * math.sin(t * 9) * push

    # puddle under the water mass
    d.ellipse([P(bx - 420, GROUND - 30), P(bx + 420, GROUND + 60)],
              fill=(*BLUE, 220), outline=(*INK, 255), width=L(6))
    # giant water dome sitting on the ground
    rx, ry = 330, 300
    d.ellipse([P(bx - rx, GROUND - ry * 2 + wobble), P(bx + rx, GROUND + 20)],
              fill=(*BLUE, 225), outline=(*INK, 250), width=L(7))
    F.poly(d, [(bx - 120, GROUND - ry * 2 + 30 + wobble), (bx - 40, GROUND - ry * 2 - 120 + wobble),
               (bx + 60, GROUND - ry * 2 + 10 + wobble)], (*BLUE, 225), (*INK, 250), 6)
    d.arc([P(bx - rx * 0.74, GROUND - ry * 2 + 30 + wobble), P(bx + rx * 0.2, GROUND - ry * 1.2 + wobble)],
          195, 330, fill=(255, 255, 255, 180), width=L(10))

    # hero leans into it and pushes with both palms
    lean = 12 * push
    pose = dict(front_leg=(-20 * push, 22 * push + 6), back_leg=(26 * push, 10),
                front_arm=(88, -6), back_arm=(74, -18),
                lean=lean, mouth="o" if push > 0.3 else "flat",
                brow=9 if push > 0.3 else 2, head=3)
    shadow(d, x, GROUND, 82)
    joints = F.hero(d, x, GROUND, h, pose)

    # palms pressed flat into the water surface
    if push > 0.05:
        for (hxp, hyp) in joints["hands"]:
            F.ellipse(d, (hxp + 6, hyp), 24, 14, SKIN_S, INK, 5)
            for i in range(3):
                d.arc([P(hxp - 30 - i * 14, hyp - 34 - i * 8), P(hxp + 16, hyp + 52 + i * 8)],
                      120, 250, fill=(*CORAL, 195), width=L(6))
        # the surface bulges but does not give way
        d.arc([P(bx - rx * 1.02, GROUND - ry * 1.55), P(bx - rx * 0.42, GROUND - 40)],
              130, 250, fill=(*INK, 190), width=L(6))
        d.arc([P(bx - rx * 0.96, GROUND - ry * 1.45), P(bx - rx * 0.5, GROUND - 70)],
              140, 240, fill=(255, 255, 255, 150), width=L(7))

    # droplets squeezed out of the blob
    if push > 0.5:
        s = clamp((push - 0.5) / 0.5)
        for i, ang in enumerate((-140, -105, -70)):
            r = 60 + 150 * s
            F.circle(d, (bx - 300 + math.cos(math.radians(ang)) * r,
                         GROUND - 120 + math.sin(math.radians(ang)) * r), 9 + 6 * (i % 2),
                     BLUE, INK, 4)


# ------------------------------------------------------------------ scene 3: cold
def scene3(d, t):
    bg_stage(d, t, "cold")
    a, b = SCENES[3]
    p = clamp((t - a) / max(0.001, b - a))
    x, h = 560.0, 320.0
    shiver = 4.0 * math.sin(t * 52) * (0.5 + 0.5 * p)
    shadow(d, x, GROUND, 84)
    pose = dict(front_leg=(-10, 20), back_leg=(12, 18),
                front_arm=(-30, 104), back_arm=(28, 100),
                head=3 * math.sin(t * 34), brow=9, mouth="flat", squash=0.94)
    F.hero(d, x + shiver, GROUND, h, pose)
    # scarf (thick, wrapped)
    F.rrect(d, (x - 52 + shiver, GROUND - h * 0.775, x + 52 + shiver, GROUND - h * 0.71),
            r=16, fill=CORAL, outline=INK, w=6)
    d.line([P(x - 40 + shiver, GROUND - h * 0.745), P(x + 40 + shiver, GROUND - h * 0.745)],
           fill=(200, 78, 56), width=L(5))
    F.poly(d, [(x + 26 + shiver, GROUND - h * 0.79), (x + 46 + shiver, GROUND - h * 0.79),
               (x + 40 + shiver, GROUND - h * 0.62), (x + 22 + shiver, GROUND - h * 0.62)],
           CORAL, INK, 6)
    # shiver ticks
    for i in range(4):
        sx = x - 96 - (i % 2) * 8 + shiver
        sy = GROUND - h * 0.62 + i * 34
        d.line([P(sx, sy), P(sx - 16, sy + 10), P(sx, sy + 20)], (*TEAL, 210), 5)
        d.line([P(x + 96 + (i % 2) * 8 + shiver, sy), P(x + 112 + shiver, sy + 10),
                P(x + 96 + shiver, sy + 20)], (*TEAL, 210), 5)
    for i in range(4):
        ph = ((t - a) / 1.0 + i / 4) % 1.0
        bx = x + 30 + 26 * ph
        by = GROUND - h * 0.80 - 170 * ph
        r = 16 + 52 * ph
        d.ellipse([P(bx - r, by - r), P(bx + r, by + r)],
                  fill=(255, 255, 255, int(160 * (1 - ph))), outline=None)
    # heat escaping upward
    for i, (ax, ay) in enumerate(((x - 120, GROUND - h * 0.95), (x - 40, GROUND - h * 1.02),
                                  (x + 40, GROUND - h * 0.98), (x + 120, GROUND - h * 0.92))):
        ph = ((t - a) * 1.1 + i * 0.25) % 1.0
        ly = ay - 120 * ph
        aa = int(210 * (1 - ph))
        d.line([P(ax, ly + 40), P(ax + 8, ly + 18), P(ax - 4, ly)], (*CORAL, aa), 7)
        d.line([P(ax - 12, ly + 10), P(ax - 4, ly), P(ax + 6, ly + 10)], (*CORAL, aa), 7)
    for i in range(6):
        cx = 110 + i * 210
        for ang in range(0, 360, 60):
            d.line([P(cx, GROUND + 26), P(cx + 30 * math.cos(math.radians(ang)),
                                          GROUND + 26 + 30 * math.sin(math.radians(ang)))],
                   (226, 246, 254), 6)
    d.rectangle([0, 0, SW, SH], fill=(120, 190, 220, 34))


# ------------------------------------------------------------------ scene 4: fall
def scene4(d, t):
    bg_stage(d, t, "table")
    a, b = SCENES[4]
    p = clamp((t - a) / max(0.001, b - a))
    x, h = 540.0, 280.0
    fu = clamp((p - 0.08) / 0.52)
    land = p > 0.60
    fy = GROUND if land else lerp(742, GROUND, ease_in(fu))
    lu = clamp((p - 0.60) / 0.14)
    squash = 1 - 0.30 * math.sin(lu * math.pi) if land else 1.0
    shadow(d, x, GROUND, 84 if land else 40)
    if land:
        pose = dict(front_arm=(-86, 16), back_arm=(86, 16), front_leg=(-24, 12),
                    back_leg=(24, 12), mouth="smile", brow=0)
    else:
        pose = dict(front_arm=(-150, -12), back_arm=(150, -12), front_leg=(-18, 34),
                    back_leg=(18, 30), mouth="o", brow=8)
    F.hero(d, x, fy, h * squash, pose)
    if not land and 0.08 < p < 0.6:
        for i in range(4):
            yy = fy - 30 - i * 48
            d.line([P(x - 66 - i * 14, yy), P(x - 40 - i * 14, yy - 54)], (*INK, 120), 7 - i)
            d.line([P(x + 66 + i * 14, yy), P(x + 40 + i * 14, yy - 54)], (*INK, 120), 7 - i)
    if land:
        s = clamp((p - 0.60) / 0.4)
        for i in range(6):
            ang = math.radians(200 + i * 24)
            r = 40 + 170 * ease_out(s)
            F.circle(d, (x + math.cos(ang) * r * 1.7, GROUND - 8 + math.sin(ang) * r * 0.35),
                     20 * (1 - s) + 3, (222, 200, 168), None, 0)
        if p > 0.78:
            d.arc([P(x + 120, GROUND - 150), P(x + 220, GROUND - 40)], 110, 250,
                  fill=(*TEAL, 220), width=L(6))


# ------------------------------------------------------------------ scene 5: ants
def scene5(d, t):
    bg_stage(d, t, "sand")
    a, b = SCENES[5]
    p = clamp((t - a) / max(0.001, b - a))
    # two small ants far behind: they set the scale
    for i in range(2):
        ax = 1150 - ((t - a) * 70 + i * 330) % 780
        F.ant(d, ax, GROUND - 74, s=1.35, flip=True, phase=t * 7 + i)
    # hero and one same-size ant, side by side
    hx_, hh_ = 470.0, 250.0
    shadow(d, hx_, GROUND, 74)
    wave = math.sin(2 * math.pi * (t - a) * 2.6)
    pose = dict(front_arm=(-150 + 10 * wave, -10), back_arm=(16, 12),
                front_leg=(-6, 5), back_leg=(6, 4), mouth="smile", head=-6)
    F.hero(d, hx_, GROUND, hh_, pose)
    # the ant stands next to him and raises a foreleg
    ax2 = 800.0
    shadow(d, ax2 - 20, GROUND + 6, 96, a=34)
    F.ant(d, ax2, GROUND - 8, s=4.3, flip=True, phase=0.0)
    d.line([P(ax2 - 44, GROUND - 96), P(ax2 - 92, GROUND - 196 + 14 * wave)], fill=INK, width=L(11))
    d.line([P(ax2 - 44, GROUND - 96), P(ax2 - 120, GROUND - 172 + 14 * wave)], fill=INK, width=L(11))
    for i in range(5):
        d.line([P(160 + i * 250, GROUND + 54), P(220 + i * 250, GROUND + 54)], (198, 160, 110), 6)


# ------------------------------------------------------------------ scene 6: question + CTA
def scene6(d, t):
    bg_stage(d, t, "yard")
    a, b = SCENES[6]
    p = clamp((t - a) / max(0.001, b - a))
    x, h = 540.0, 360.0
    shadow(d, x, GROUND, 96)
    wave = math.sin(2 * math.pi * (t - a) * 2.4)
    pose = dict(front_arm=(-152 + 14 * wave, -6), back_arm=(18, 12),
                front_leg=(-6, 5), back_leg=(6, 4), mouth="smile", head=2 * wave)
    F.hero(d, x, GROUND, h, pose)
    if p > 0.10:
        u = back_out((p - 0.10) / 0.30)
        qs = 170 * u
        qx, qy = 265, GROUND - 640
        d.arc([P(qx - qs * 0.5, qy - qs * 0.55), P(qx + qs * 0.5, qy + qs * 0.25)],
              195, 15, fill=CORAL, width=L(30))
        d.line([P(qx, qy + qs * 0.2), P(qx, qy + qs * 0.42)], CORAL, 30)
        F.circle(d, (qx, qy + qs * 0.62), 18, CORAL, None, 0)
    for i in range(16):
        ph = ((t - a) * 0.75 + i * 0.29) % 1.0
        cx = 70 + (i * 157) % 1360
        cy = 160 + ph * 1000
        F.circle(d, (cx, cy), 12, [CORAL, MUSTARD, TEAL, BLUE][i % 4], None, 0)


# ------------------------------------------------------------------ UI
CAPS = [
    (1, "Крошка в 50 раз тяжелее тебя"),
    (2, "Вода — как бетон: не протолкнёшься"),
    (3, "Тепло улетает в 100 раз быстрее"),
    (4, "Падать не страшно: как с дивана"),
    (5, "Муравьи на Земле уже 100 млн лет"),
    (6, "А что бы ты сделал первым?"),
]
STICK = {
    1: ("×100 СИЛА", 4.6, TEAL),
    2: ("ВОДА = БЕТОН", 2.1, CORAL),
    3: ("ТЕПЛО ×100", 3.2, TEAL),
    4: ("МЯГКО", 1.5, CORAL),
}


def ui_layer(t):
    lay = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a0, b0 = SCENES[0]
    if a0 <= t <= b0 + 0.15:
        rows = [("ЧТО, ЕСЛИ", 62, INK), ("ТЫ СТАНЕШЬ", 62, INK), ("С МУРАВЬЯ?", 78, CORAL)]
        p = clamp((t - a0) / max(0.001, b0 - a0))
        for i, (txt, size, col) in enumerate(rows):
            if p > i * 0.10:
                aa = int(255 * clamp((p - i * 0.10) / 0.16))
                d.text(P(W / 2, 330 + i * 84), txt, font=font(size), fill=(*col, aa), anchor="mm")
        if p > 0.55:
            txt = "×1" if p < 0.62 else ("×1/10" if p < 0.72 else "×1/300")
            F.plate(d, (760, 210, 1010, 322), r=24, fill=MUSTARD, bw=6)
            d.text(P(885, 266), txt, font=font(54), fill=INK, anchor="mm")
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
            im = F.sticker(txt, 46, col, rot_=-4 if i % 2 else 3)
            if u < 1:
                im = im.resize((max(2, int(im.width * u)), max(2, int(im.height * u))), Image.LANCZOS)
            lay.alpha_composite(im, (int(CW * 0.5 - im.width / 2), int(300 * U)))
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
SCENE_FN = [scene0, scene1, scene2, scene3, scene4, scene5, scene6]
CAMS = [Cam(720, 1150, 1.02), Cam(520, 1280, 1.03), Cam(540, 1250, 1.04),
        Cam(600, 1265, 1.05), Cam(540, 1250, 1.00), Cam(650, 1300, 1.06),
        Cam(540, 1220, 1.00)]


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
    cam = Cam(base.cx + 10 * math.sin(2 * math.pi * t / 9.0), base.cy - 18 * p,
              base.z * (1 + 0.035 * p))
    x0, y0, vw, vh = cam.view()
    crop = scene.crop((int(x0 * U), int(y0 * U), int((x0 + vw) * U), int((y0 + vh) * U)))
    frame = crop.resize((CW, CH), Image.LANCZOS).convert("RGBA")
    frame.alpha_composite(ui_layer(t))
    return frame.convert("RGB").resize((W, H), Image.LANCZOS)


def frame_at(t):
    return compose(t)


def _work(i):
    return i, frame_at(i / FPS).tobytes()


def render_all(workers=3):
    os.makedirs("frames", exist_ok=True)
    n = int(round(DUR * FPS))
    done = {int(f[1:5]) for f in os.listdir("frames") if f.startswith("f")}
    todo = [i for i in range(n) if i not in done]
    print(f"frames {len(done)}/{n}, todo {len(todo)}, DUR={DUR:.2f}", flush=True)
    if not todo:
        return
    from multiprocessing import Pool
    with Pool(workers) as pool:
        for k, (i, buf) in enumerate(pool.imap_unordered(_work, todo, chunksize=4)):
            Image.frombytes("RGB", (W, H), buf).save(f"frames/f{i:04d}.png")
            if k % 60 == 0:
                print(f"{k}/{len(todo)}", flush=True)
    print("frames done", flush=True)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        os.makedirs("preview", exist_ok=True)
        ts = [0.8, 1.6, 2.5, 3.8, 5.6, 7.4, 8.9, 10.2, 11.6, 13.3, 15.2, 17.1,
              18.8, 20.6, 22.6, 24.6]
        sheet = Image.new("RGB", (300 * 4, 533 * 4), (24, 24, 26))
        for i, t in enumerate(ts):
            im = frame_at(t).resize((300, 533), Image.LANCZOS)
            sheet.paste(im, ((i % 4) * 300, (i // 4) * 533))
        sheet.save("preview/sheet.png")
        for t in (1.6, 6.4, 10.2, 13.3, 16.6, 24.6):
            frame_at(t).save(f"preview/full_{t}.png")
        print("preview ok", len(ts))
    elif "--render" in sys.argv:
        workers = int(S.get("video.workers", 3))
        if "--workers" in sys.argv:
            workers = int(sys.argv[sys.argv.index("--workers") + 1])
        render_all(workers)
