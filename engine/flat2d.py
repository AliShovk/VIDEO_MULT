"""Flat 2D cartoon: «Что, если ты станешь размером с муравья?» 1080x1920, 30 fps.

Everything is drawn with flat fills + ink outlines on a supersampled canvas,
posed from a tiny FK rig. Scene = pure function of time.
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import settings as S  # noqa: E402

CFG = S.CFG
W = int(S.get("video.width", 1080))
H = int(S.get("video.height", 1920))
U = float(S.get("video.supersample", 1.5))   # supersample factor
CW, CH = int(W * U), int(H * U)
FPS = int(S.get("video.fps", 30))

INK = tuple(S.rgb("ink") or (28, 34, 38))
CREAM = tuple(S.rgb("cream") or (247, 233, 212))
CREAM_D = tuple(S.rgb("cream_d") or (236, 218, 192))
FLOOR = tuple(S.rgb("floor") or (226, 203, 170))
CORAL = tuple(S.rgb("coral") or (241, 106, 78))
MUSTARD = tuple(S.rgb("mustard") or (244, 181, 65))
TEAL = tuple(S.rgb("teal") or (47, 163, 155))
TEAL_D = tuple(S.rgb("teal_d") or (36, 128, 122))
SKY = tuple(S.rgb("sky") or (191, 226, 236))
WHITE = tuple(S.rgb("white") or (255, 250, 242))
BLUE = tuple(S.rgb("blue") or (127, 200, 232))
SAND = tuple(S.rgb("sand") or (232, 199, 143))
GREEN = tuple(S.rgb("green") or (58, 122, 92))

FONT_B = S.get("fonts.bold", "C:/Windows/Fonts/segoeuib.ttf")
FONT_R = S.get("fonts.regular", "C:/Windows/Fonts/segoeui.ttf")
_fonts = {}


def font(size, bold=True):
    key = (round(size, 1), bold)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(FONT_B if bold else FONT_R, max(6, int(size * U)))
    return _fonts[key]


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = clamp(x)
    return x * x


def back_out(x, s=2.0):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def P(x, y):
    return (x * U, y * U)


def L(v):
    return max(1, int(round(v * U)))


# ------------------------------------------------------------------ primitives
def line(d, pts, fill=INK, w=6, joint="curve"):
    d.line([P(*p) for p in pts], fill=fill, width=L(w), joint=joint)


def circle(d, xy, r, fill, outline=INK, w=6):
    x, y = xy
    d.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=fill, outline=outline, width=L(w))


def ellipse(d, xy, rx, ry, fill, outline=INK, w=6):
    x, y = xy
    d.ellipse([P(x - rx, y - ry), P(x + rx, y + ry)], fill=fill, outline=outline, width=L(w))


def rrect(d, box, r, fill, outline=INK, w=6):
    x0, y0, x1, y1 = box
    d.rounded_rectangle([P(x0, y0), P(x1, y1)], radius=L(r), fill=fill,
                        outline=outline, width=L(w) if outline else 0)


def poly(d, pts, fill, outline=INK, w=6, close=True):
    pp = [P(*p) for p in pts]
    d.polygon(pp, fill=fill)
    if outline:
        d.line(pp + [pp[0]] if close else pp, fill=outline, width=L(w), joint="curve")


def capsule(d, p1, p2, w, fill, outline=INK, ow=6, w2=None):
    """Limb segment with round caps and an optional taper towards p2."""
    x1, y1 = p1
    x2, y2 = p2
    r1 = w / 2
    r2 = (w2 if w2 is not None else w) / 2
    ang = math.atan2(y2 - y1, x2 - x1)
    nx, ny = -math.sin(ang), math.cos(ang)
    quad = [(x1 + nx * r1, y1 + ny * r1), (x2 + nx * r2, y2 + ny * r2),
            (x2 - nx * r2, y2 - ny * r2), (x1 - nx * r1, y1 - ny * r1)]
    poly(d, quad, fill, outline, ow, close=True)
    circle(d, p1, r1, fill, outline, ow)
    circle(d, p2, r2, fill, outline, ow)
    poly(d, quad, fill, None, 0, close=True)


def shadow_blob(d, xy, rx, ry, a=42):
    x, y = xy
    d.ellipse([P(x - rx, y - ry), P(x + rx, y + ry)], fill=(INK[0], INK[1], INK[2], a))


# ------------------------------------------------------------------ hero rig
def rot(p, ang, origin=(0, 0)):
    a = math.radians(ang)
    x, y = p[0] - origin[0], p[1] - origin[1]
    return (origin[0] + x * math.cos(a) - y * math.sin(a),
            origin[1] + x * math.sin(a) + y * math.cos(a))


HERO_H = 300.0
HIP_Y, SH_Y, HEAD_Y = -112.0, -206.0, -252.0
SH_X = 36.0
HIP_X = 19.0
UP_ARM, FORE_ARM = 47.0, 45.0
THIGH, SHIN = 56.0, 52.0


def hero(d, x, y, h, pose, flip=False, alpha=255):
    """Draw the flat 2D character with feet at (x, y); h = full height."""
    k = h / HERO_H
    sgn = -1 if flip else 1

    def T(p):
        return (x + p[0] * k * sgn, y + p[1] * k)

    ang = pose
    lean = ang.get("lean", 0)
    sq = ang.get("squash", 1.0)

    def limb(origin, a0, a1, l0, l1, w, fill):
        a = math.radians(a0)
        p1 = (origin[0] + math.sin(a) * l0, origin[1] + math.cos(a) * l0)
        a2 = math.radians(a0 + a1)
        p2 = (p1[0] + math.sin(a2) * l1, p1[1] + math.cos(a2) * l1)
        capsule(d, T(origin), T(p1), w * k, fill, w2=(w - 4) * k)
        capsule(d, T(p1), T(p2), (w - 4) * k, fill, w2=(w - 9) * k)
        return p2

    # ---- legs (back leg first, darker)
    back_leg = ang.get("back_leg", (4, 8))
    p_back = limb((HIP_X, HIP_Y - 4), back_leg[0], back_leg[1], THIGH, SHIN, 27, (SKIN_D))
    _shoe(d, T(p_back), k, flip, shade=True)
    # ---- back arm
    b_arm = ang.get("back_arm", (8, 12))
    p_ba = limb((SH_X - 4, SH_Y + 6), b_arm[0], b_arm[1], UP_ARM, FORE_ARM, 24, TEAL_D)
    _hand(d, T(p_ba), 11 * k, SKIN_D, mirrored=False)

    # ---- torso
    hipL, hipR = (-HIP_X, HIP_Y), (HIP_X, HIP_Y)
    shL, shR = (-SH_X, SH_Y), (SH_X, SH_Y)
    torso = [hipL, shL, (0, SH_Y - 16), shR, hipR]
    torso = [rot(p, lean) for p in torso]
    poly(d, [T(p) for p in torso], MUSTARD, INK, 6)
    # shirt detail: collar + pocket
    collar = [rot(p, lean) for p in [(-14, SH_Y - 6), (0, SH_Y + 18), (14, SH_Y - 6)]]
    poly(d, [T(p) for p in collar], CORAL, INK, 5, close=True)
    rrect_box = [rot(p, lean) for p in [(-16, SH_Y + 34), (-2, SH_Y + 62)]]
    poly(d, [T(p) for p in rrect_box] + [T(rot((16, SH_Y + 62), lean)), T(rot((2, SH_Y + 34), lean))],
         TEAL, INK, 4)

    # ---- front leg
    f_leg = ang.get("front_leg", (-4, 6))
    p_front = limb((-HIP_X, HIP_Y), f_leg[0], f_leg[1], THIGH, SHIN, 28, SKIN)
    _shoe(d, T(p_front), k, flip)

    # ---- head
    head_tilt = ang.get("head", 0)
    hx, hy = rot((0, HEAD_Y), lean + head_tilt, (0, SH_Y))
    hx += 0
    d.rectangle([P(x + (-13) * k, y + (hy + 30) * k), P(x + 13 * k, y + (SH_Y + 8) * k)],
                fill=SKIN_D, outline=INK, width=L(5))
    circle(d, T((hx, hy + 2)), 43 * k, SKIN, INK, 6)
    # hair: flat cap shape
    hair = [(hx - 44, hy - 6), (hx - 34, hy - 40), (hx + 34, hy - 40), (hx + 44, hy - 6),
            (hx + 26, hy - 16), (hx - 26, hy - 16)]
    poly(d, [T(p) for p in hair], (54, 44, 40), INK, 6)
    _face(d, T((hx, hy)), abs(k), ang)

    # ---- front arm
    f_arm = ang.get("front_arm", (-8, 10))
    p_fa = limb((-SH_X + 4, SH_Y + 6), f_arm[0], f_arm[1], UP_ARM, FORE_ARM, 25, TEAL)
    _hand(d, T(p_fa), 12 * k, SKIN, mirrored=True)
    return {"hands": [T(p_ba), T(p_fa)], "head": T((hx, hy)),
            "waist": T((0, HIP_Y)), "feet": (x, y)}


def _hand(d, p, r, fill, mirrored=False):
    """Palm + thumb instead of a plain circle, so grips read at small sizes."""
    x, y = p
    rx, ry = r * 1.05, r * 1.25
    d.ellipse([P(x - rx, y - ry), P(x + rx, y + ry)], fill=fill, outline=INK, width=L(5))
    sx = 1 if mirrored else -1
    d.line([P(x + sx * rx * 0.7, y - ry * 0.2), P(x + sx * rx * 1.5, y - ry * 0.9)],
           fill=fill, width=max(2, L(r * 0.55)))
    d.line([P(x + sx * rx * 0.7, y - ry * 0.2), P(x + sx * rx * 1.5, y - ry * 0.9)],
           fill=INK, width=max(1, L(2)))


SKIN = (243, 202, 162)
SKIN_D = (214, 168, 130)


def _shoe(d, p, k, flip, shade=False):
    x, y = p
    w, h = 30 * k, 15 * k
    box = [x - w * 0.5, y - h * 0.5, x + w * 0.62, y + h * 0.5]
    rrect(d, box, 6 * k, (92, 74, 66) if shade else (58, 46, 42), INK, 5)
    d.line([P(box[0] + w * 0.06, y + h * 0.34), P(box[2] - w * 0.06, y + h * 0.34)],
           (232, 226, 214), max(1, L(3)))


def _face(d, c, k, pose):
    """k is negative when the hero is flipped, which mirrors the face."""
    x, y = c
    ex = 15 * abs(k)
    ey = -6 * k
    eyes = pose.get("eyes", "open")
    if eyes == "closed":
        line(d, [(x - ex - 5 * abs(k), y + ey), (x - ex + 5 * abs(k), y + ey)], INK, 4.5)
        line(d, [(x + ex - 5 * abs(k), y + ey), (x + ex + 5 * abs(k), y + ey)], INK, 4.5)
    else:
        er = 8.2 * abs(k)
        look = pose.get("look", 0) * abs(k)
        for sx in (-1, 1):
            cx = x + sx * ex
            d.ellipse([P(cx - er, y + ey - er * 1.15), P(cx + er, y + ey + er * 1.15)],
                      fill=WHITE, outline=INK, width=L(3))
            d.ellipse([P(cx - er * 0.55 + look, y + ey - er * 0.55), P(cx + er * 0.55 + look, y + ey + er * 0.55)],
                      fill=INK, outline=None, width=0)
            d.ellipse([P(cx - er * 0.55 + look - er * 0.22, y + ey - er * 0.4),
                       P(cx - er * 0.55 + look + er * 0.05, y + ey - er * 0.12)],
                      fill=WHITE, outline=None, width=0)
    b = pose.get("brow", 0)
    line(d, [(x - ex - 8 * abs(k), y + ey - (12 + b) * abs(k)), (x - ex + 6 * abs(k), y + ey - (9 + b * 0.4) * abs(k))], INK, 4.5)
    line(d, [(x + ex - 6 * abs(k), y + ey - (9 + b * 0.4) * abs(k)), (x + ex + 8 * abs(k), y + ey - (12 + b) * abs(k))], INK, 4.5)
    mouth = pose.get("mouth", "smile")
    if mouth == "o":
        ellipse(d, (x, y + 20 * abs(k)), 8 * abs(k), 10 * abs(k), (70, 44, 40), INK, 4)
    elif mouth == "flat":
        line(d, [(x - 10 * abs(k), y + 21 * abs(k)), (x + 10 * abs(k), y + 21 * abs(k))], INK, 4)
    elif mouth == "frown":
        line(d, [(x - 11 * abs(k), y + 24 * abs(k)), (x, y + 17 * abs(k)), (x + 11 * abs(k), y + 24 * abs(k))], INK, 4)
    else:
        line(d, [(x - 11 * abs(k), y + 16 * abs(k)), (x, y + 25 * abs(k)), (x + 11 * abs(k), y + 16 * abs(k))], INK, 4)


# ------------------------------------------------------------------ props
def crumb(d, x, y, s, rot_=0):
    pts = []
    rng = [(0, 0), (0.55, -0.18), (1.0, 0.05), (0.85, 0.55), (0.95, 0.9), (0.45, 1.0), (0.05, 0.82), (-0.08, 0.35)]
    for i, (a, b) in enumerate(rng):
        px = (a - 0.45) * s
        py = (b - 0.5) * s * 0.72
        rt = math.radians(rot_)
        pts.append((x + px * math.cos(rt) - py * math.sin(rt), y + px * math.sin(rt) + py * math.cos(rt)))
    poly(d, pts, (216, 165, 100), INK, 6)
    for i in range(5):
        circle(d, (x + (i - 2) * s * 0.16, y - s * 0.1 + (i % 2) * s * 0.18), s * 0.035,
               (188, 138, 78), None, 0)


def droplet(d, x, y, r, flat=1.0, alpha=205):
    # teardrop: round bottom + pointed top
    d.ellipse([P(x - r, y - r), P(x + r, y + r * flat)],
              fill=(*BLUE, alpha), outline=(*INK, alpha))
    poly(d, [(x - r * 0.62, y - r * 0.55), (x, y - r * 1.9), (x + r * 0.62, y - r * 0.55)],
         (*BLUE, alpha), (*INK, alpha), 5)


def ice_cube(d, x, y, s):
    rrect(d, [x - s / 2, y - s / 2, x + s / 2, y + s / 2], s * 0.12, (190, 226, 240), INK, 6)
    line(d, [(x - s * 0.28, y - s * 0.28), (x - s * 0.05, y - s * 0.05)], (255, 255, 255), 7)
    line(d, [(x - s * 0.36, y + s * 0.1), (x - s * 0.12, y + s * 0.3)], (255, 255, 255), 5)


def ant(d, x, y, s=1.0, flip=False, phase=0.0):
    sg = -1 if flip else 1
    wig = math.sin(phase) * 3

    def T(px, py):
        return (x + px * s * sg, y + py * s)

    # legs
    for i, (lx, ly) in enumerate([(-14, 0), (0, 2), (14, 0)]):
        line(d, [T(lx, -8), T(lx - 6 + wig, 8), T(lx - 10 + wig, 14)], INK, max(2, 3 * s))
    # body: three blobs
    for (bx, by, r) in [(26, -14, 9), (8, -16, 11), (-12, -14, 12)]:
        circle(d, T(bx, by), r * s, (54, 40, 36) if bx > 0 else (74, 54, 46), INK, max(2, 3 * s))
    # antennae
    line(d, [T(34, -16), T(44, -30)], INK, max(2, 2.5 * s))
    line(d, [T(36, -12), T(48, -22)], INK, max(2, 2.5 * s))


# ------------------------------------------------------------------ text
def plate(d, box, r=26, fill=WHITE, border=INK, bw=6, shadow=10, shadow_a=40):
    x0, y0, x1, y1 = box
    if shadow:
        d.rounded_rectangle([P(x0 + shadow, y0 + shadow), P(x1 + shadow, y1 + shadow)],
                            radius=L(r), fill=(*INK, shadow_a))
    d.rounded_rectangle([P(x0, y0), P(x1, y1)], radius=L(r), fill=fill,
                        outline=border, width=L(bw) if border else 0)


def text_c(d, xy, s, size, fill=INK, fnt=None, stroke=0, stroke_fill=INK):
    d.text(P(*xy), s, font=fnt or font(size), fill=fill, anchor="mm",
           stroke_width=L(stroke), stroke_fill=stroke_fill)


def wrap(d, text, fnt, maxw):
    out = []
    for para in text.split("\n"):
        words, line = para.split(), ""
        for w in words:
            probe = (line + " " + w).strip()
            if d.textlength(probe, font=fnt) <= maxw * U or not line:
                line = probe
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def caption(d, t, t0, t1, text, hl=(), y=1560, w=880):
    if not (t0 <= t <= t1):
        return
    a = min(1.0, (t - t0) / 0.18, (t1 - t) / 0.18)
    if a <= 0:
        return
    fnt = font(52)
    tmp = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    lines = wrap(td, text, fnt, w - 70)
    lh = 66
    h = lh * len(lines) + 52
    x0 = (W - w) / 2
    pop = 0.97 + 0.03 * ease_out((t - t0) / 0.18)
    lay = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    plate(ld, (x0, y - h / 2, x0 + w, y + h / 2), r=30, fill=(255, 249, 238), bw=6)
    for i, ln in enumerate(lines):
        yy = y - h / 2 + 26 + lh * i + lh / 2
        ld.text(P(W / 2, yy), ln, font=fnt, fill=(*INK, 255), anchor="mm")
    if a < 1:
        al = lay.split()[3].point(lambda v: int(v * a))
        lay.putalpha(al)
    if pop != 1.0:
        lay = lay.resize((int(CW * pop), int(CH * pop)), Image.LANCZOS)
        tmp.alpha_composite(lay, ((CW - lay.width) // 2, (CH - lay.height) // 2))
    else:
        tmp.alpha_composite(lay)
    return tmp


STICKERS = {}


def sticker(text, size, fill, rot_=0, pad=20):
    key = (text, size, fill, rot_, pad)
    if key in STICKERS:
        return STICKERS[key]
    f = font(size)
    tmp = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    tw = d.textlength(text, font=f) / U
    w, h = tw + 2 * pad, size + 2 * pad
    im = Image.new("RGBA", (L(w) + 4, L(h) + 4), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([L(2), L(2), L(w + 2), L(h + 2)], radius=L(18), fill=fill,
                         outline=INK, width=L(6))
    dd.text((im.width / 2, im.height / 2), text, font=f, anchor="mm", fill=(255, 255, 255))
    if rot_:
        im = im.rotate(rot_, expand=True, resample=Image.BICUBIC)
    STICKERS[key] = im
    return im


# ------------------------------------------------------------------ timeline
VOICE_DIR = S.get("paths.voice_dir", "voice")
LINES_PATH = os.path.join(VOICE_DIR, "lines.json")
LINES = json.load(open(LINES_PATH, encoding="utf-8"))
GAP = float(S.get("timeline.gap", 0.26))
T = []
_t = 0.35
for i, ln in enumerate(LINES):
    T.append({"start": _t, "end": _t + ln["dur"], "line": ln["text"], "file": ln["file"]})
    _t += ln["dur"] + GAP
SPEECH_END = T[-1]["end"]
DUR = max(float(S.get("timeline.min_duration", 25.0)),
          SPEECH_END + float(S.get("timeline.tail", 2.0)))
for i in range(len(T)):
    if i + 1 < len(T):
        T[i]["gap_end"] = T[i + 1]["start"]
    else:
        T[i]["gap_end"] = DUR


def scene_span(i, pad=0.18):
    a = T[i]["start"] - pad
    b = (T[i + 1]["start"] - pad) if i + 1 < len(T) else DUR
    return max(0.0, a), min(DUR, b)


SCENES = [scene_span(i) for i in range(len(T))]


# ------------------------------------------------------------------ grain
_GRAIN = {}


def grain(img_rgb, seed=0, amount=0.35):
    """Film grain so flat fills do not look like plastic."""
    import numpy as np
    if seed not in _GRAIN:
        rng = np.random.default_rng(100 + seed)
        _GRAIN[seed] = rng.normal(0, 11, (H // 4, W // 4, 1)).astype(np.float32)
    g = _GRAIN[seed]
    small = Image.fromarray(np.repeat(np.clip(g + 128, 0, 255).astype(np.uint8), 3, axis=2))
    big = small.resize(img_rgb.size, Image.NEAREST)
    a = np.asarray(img_rgb).astype(np.float32)
    b = np.asarray(big).astype(np.float32) - 128.0
    return Image.fromarray(np.clip(a + b * amount, 0, 255).astype(np.uint8))
