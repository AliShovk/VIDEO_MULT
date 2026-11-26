"""Music, SFX and the mixed soundtrack for the gravity-loss episode."""
import json
import math
import os
import sys
import wave

import numpy as np
from scipy.signal import butter, lfilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import settings as S  # noqa: E402

SR = 44100
VOICE_DIR = S.get("paths.voice_dir", "voice")
LINES = json.load(open(os.path.join(VOICE_DIR, "lines.json"), encoding="utf-8"))
GAP = float(S.get("timeline.gap", 0.2))
BPM = float(S.get("audio.bpm", 96))

starts, t = [], 0.35
for ln in LINES:
    starts.append(t)
    t += ln["dur"] + GAP
SPEECH_END = starts[-1] + LINES[-1]["dur"]
DUR = max(float(S.get("timeline.min_duration", 25.0)), SPEECH_END + float(S.get("timeline.tail", 1.4)))
N = int(DUR * SR)
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(31)

music = np.zeros(N, np.float32)
sfx = np.zeros(N, np.float32)


def add(buf, sig, t0, gain=1.0):
    i0 = int(t0 * SR)
    if i0 >= N or i0 < 0:
        return
    sig = sig[: max(0, N - i0)]
    buf[i0:i0 + len(sig)] += sig * gain


def env(n, a=0.004, d=0.2):
    tt = np.arange(n) / SR
    return np.clip(tt / max(1e-4, a), 0, 1) * np.exp(-tt / max(1e-4, d))


def tone(f, dur, kind="sine"):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    if kind == "sine":
        return np.sin(2 * np.pi * f * tt)
    if kind == "tri":
        out = np.zeros(n, np.float32)
        for k in range(6):
            fk = f * (2 * k + 1)
            if fk > SR / 2.2:
                break
            out += ((-1) ** k) * np.sin(2 * np.pi * fk * tt) / (2 * k + 1) ** 2
        return out * 0.8
    out = np.zeros(n, np.float32)
    for h in range(1, 10):
        if f * h > SR / 2.2:
            break
        out += np.sin(2 * np.pi * f * h * tt) / h
    return out * 0.6


def lp(x, fc, order=2):
    b, a = butter(order, min(0.99, fc / (SR / 2)), btype="low")
    return lfilter(b, a, x).astype(np.float32)


def hp(x, fc, order=2):
    b, a = butter(order, min(0.99, fc / (SR / 2)), btype="high")
    return lfilter(b, a, x).astype(np.float32)


def kick(g=1.0, dur=0.34):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 110 * np.exp(-tt * 24) + 38
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 6.5)
    click = rng.normal(0, 1, n) * np.exp(-tt * 220) * 0.2
    return np.tanh((body + click) * 1.7) * g


def clap(g=1.0, dur=0.2):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    return np.tanh(hp(rng.normal(0, 1, n), 1400) * np.exp(-tt * 24) * 1.2) * g


def hat(g=0.18, dur=0.06, open_=False):
    n = int(dur * SR * (3 if open_ else 1))
    tt = np.arange(n) / SR
    return hp(rng.normal(0, 1, n), 6500) * np.exp(-tt * (30 if not open_ else 12)) * g


def pluck(f, dur=0.35, g=1.0):
    s = tone(f, dur, "tri") + 0.25 * tone(f * 2.01, dur, "sine")
    return s * env(len(s), 0.003, 0.15) * g


def marimba(f, dur=0.4, g=1.0):
    s = tone(f, dur, "sine") + 0.35 * tone(f * 4, dur, "sine") + 0.15 * tone(f * 9.1, dur, "sine")
    return s * env(len(s), 0.002, 0.11) * g


def bass(f, dur, g=1.0):
    return lp(tone(f, dur, "saw"), 260) * env(int(dur * SR), 0.008, 0.4) * g


def sweep(dur, f0, f1, g=1.0, bands=10):
    n = int(dur * SR)
    noise = rng.normal(0, 1, n).astype(np.float32)
    out = np.zeros(n, np.float32)
    chunk = max(1, n // bands)
    for k in range(bands):
        cut = f0 * (f1 / f0) ** (k / max(1, bands - 1))
        seg = lfilter(*butter(2, min(0.99, cut / (SR / 2)), btype="low"),
                      noise[max(0, k * chunk - chunk // 2): min(n, (k + 1) * chunk + chunk // 2)])
        lo, hi = k * chunk, min(n, (k + 1) * chunk)
        out[lo:hi] = seg[chunk // 2: chunk // 2 + (hi - lo)][: hi - lo]
    tt = np.arange(n) / SR
    e = np.clip(tt / 0.04, 0, 1) * np.clip((dur - tt) / (dur * 0.7), 0, 1)
    return out * e * 4 * g


def click(g=1.0):
    n = int(0.05 * SR)
    tt = np.arange(n) / SR
    return (rng.normal(0, 1, n) * np.exp(-tt * 260)) * g


NOTE = {"A1": 55.0, "A2": 110.0, "C3": 130.81, "E3": 164.81, "F2": 87.31, "G2": 98.0,
        "B2": 123.47, "D3": 146.83, "A3": 220.0, "C4": 261.63, "E4": 329.63, "F4": 349.23,
        "G4": 392.0, "B3": 246.94, "D4": 293.66, "A4": 440.0, "C5": 523.25}

CHORDS = [("Am", ["A2", "C3", "E3"], ["A4", "C5", "E5" if False else "A4"], "A1"),
          ("F", ["F2", "A2", "C3"], ["F4", "A4", "C5"], "F2"),
          ("C", ["C3", "E3", "A3"], ["E4", "A4", "C5"], "C3"),
          ("G", ["G2", "B2", "D3"], ["D4", "G4", "B3"], "G2")]

nbar = int(math.ceil(DUR / BAR))
prog = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
for bar in range(nbar):
    t0 = bar * BAR
    if t0 >= DUR:
        break
    name, ch, arp, root = CHORDS[prog[bar % len(prog)]]
    add(music, kick(0.9), t0)
    add(music, kick(0.75), t0 + 1.75 * BEAT)
    add(music, clap(0.4), t0 + BEAT)
    add(music, clap(0.44), t0 + 3 * BEAT)
    for i in range(8):
        add(music, hat(0.12 if i % 2 else 0.18), t0 + i * BEAT / 2)
    add(music, hat(0.14, open_=True), t0 + 3.5 * BEAT)
    add(music, bass(NOTE[root], 0.5, 0.85), t0)
    add(music, bass(NOTE[root], 0.3, 0.6), t0 + 1.75 * BEAT)
    add(music, bass(NOTE[ch[2]], 0.3, 0.5), t0 + 2.75 * BEAT)
    for i in range(8):
        add(music, marimba(NOTE[arp[i % len(arp)]], 0.4, 0.11), t0 + i * BEAT / 2)

# ---------------------------------------------------------------- sfx
add(sfx, click(0.8), 0.05)
add(sfx, sweep(0.5, 400, 5000, 0.35), 0.05)
# the switch flips off
off_t = starts[0] + (LINES[0]["dur"] * 0.35)
add(sfx, click(1.0), off_t)
add(sfx, kick(0.5, 0.2), off_t)
# everything starts to float: rising shimmer
add(sfx, sweep(0.9, 900, 7000, 0.28), off_t + 0.15)
# fling: wind + rumble
add(sfx, sweep(1.6, 300, 2500, 0.5), starts[1] - 0.1)
add(sfx, lp(rng.normal(0, 1, int(1.4 * SR)), 180) * env(int(1.4 * SR), 0.05, 0.9) * 1.5, starts[1])
# air escaping
add(sfx, sweep(1.4, 4000, 600, 0.45), starts[2] + 0.2)
add(sfx, hp(rng.normal(0, 1, int(1.6 * SR)), 2500) * env(int(1.6 * SR), 0.2, 0.9) * 0.5, starts[2] + 0.1)
# heartbeat under the blood scene
for k in range(6):
    tt = starts[3] + 0.4 + k * 0.52
    add(sfx, kick(0.55, 0.22), tt)
    add(sfx, kick(0.35, 0.18), tt + 0.16)
# vertigo: wobbling tone
n_v = int(1.6 * SR)
tv = np.arange(n_v) / SR
vib = np.sin(2 * np.pi * 220 * tv * (1 + 0.06 * np.sin(2 * np.pi * 1.5 * tv)))
add(sfx, (vib * env(n_v, 0.05, 0.7) * 0.16).astype(np.float32), starts[4] + 0.2)
# planet cracks: deep rumbles + snaps
for k in range(4):
    tt = starts[5] + 0.3 + k * 0.42
    add(sfx, kick(1.0, 0.5), tt)
    add(sfx, lp(rng.normal(0, 1, int(0.5 * SR)), 140) * env(int(0.5 * SR), 0.004, 0.25) * 1.6, tt)
    add(sfx, click(0.5), tt + 0.05)
# finale chime
for i, f in enumerate((523.25, 659.26, 783.99)):
    add(sfx, tone(f, 1.1, "sine") * env(int(1.1 * SR), 0.01, 0.45) * 0.14, starts[6] + 1.9 + i * 0.09)


def rms(x):
    return float(np.sqrt((x ** 2).mean()) + 1e-9)


voice = np.zeros(N, np.float32)
for ln, st in zip(LINES, starts):
    w = wave.open(ln["file"], "rb")
    a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    if w.getnchannels() == 2:
        a = a.reshape(-1, 2).mean(1)
    voice[int(st * SR): int(st * SR) + len(a)] += a[: max(0, N - int(st * SR))]

music_g = float(S.get("audio.music_rms", 0.026)) / rms(music)
sfx_g = float(S.get("audio.sfx_rms", 0.048)) / rms(sfx)
voice_g = float(S.get("audio.voice_rms", 0.15)) / rms(voice)
print("gains", round(music_g, 3), round(sfx_g, 3), round(voice_g, 3))

mix = music * music_g + sfx * sfx_g + voice * voice_g
mix = np.tanh(mix * 1.15) * 0.93
fi = int(0.06 * SR)
mix[:fi] *= np.linspace(0, 1, fi)
fo = int(0.5 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)
st = np.stack([mix, np.concatenate([np.zeros(160, np.float32), mix[:-160]]) * 0.99], axis=1)
pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
out_wav = S.get("paths.audio", "audio/mix.wav")
os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
with wave.open(out_wav, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("mix.wav", round(len(mix) / SR, 2), "s | DUR", round(DUR, 2))
