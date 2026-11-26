"""Music, SFX and the mixed soundtrack for the ant-scale flat cartoon."""
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
GAP = float(S.get("timeline.gap", 0.26))
starts, t = [], 0.35
for ln in LINES:
    starts.append(t)
    t += ln["dur"] + GAP
SPEECH_END = starts[-1] + LINES[-1]["dur"]
DUR = max(25.0, SPEECH_END + 2.0)
N = int(DUR * SR)
BPM = float(S.get("audio.bpm", 96))
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(23)

music = np.zeros(N, np.float32)
sfx = np.zeros(N, np.float32)


def add(buf, sig, t0, gain=1.0):
    i0 = int(t0 * SR)
    if i0 >= N or i0 < 0:
        return
    sig = sig[: max(0, N - i0)]
    buf[i0:i0 + len(sig)] += sig * gain


def env(n, a=0.004, d=0.2):
    t = np.arange(n) / SR
    return np.clip(t / max(1e-4, a), 0, 1) * np.exp(-t / max(1e-4, d))


def tone(f, dur, kind="sine"):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "sine":
        return np.sin(2 * np.pi * f * t)
    if kind == "tri":
        out = np.zeros(n, np.float32)
        for k in range(6):
            fk = f * (2 * k + 1)
            if fk > SR / 2.2:
                break
            out += ((-1) ** k) * np.sin(2 * np.pi * fk * t) / (2 * k + 1) ** 2
        return out * 0.8
    out = np.zeros(n, np.float32)
    for h in range(1, 10):
        if f * h > SR / 2.2:
            break
        out += np.sin(2 * np.pi * f * h * t) / h
    return out * 0.6


def lp(x, fc, order=2):
    b, a = butter(order, min(0.99, fc / (SR / 2)), btype="low")
    return lfilter(b, a, x).astype(np.float32)


def hp(x, fc, order=2):
    b, a = butter(order, min(0.99, fc / (SR / 2)), btype="high")
    return lfilter(b, a, x).astype(np.float32)


def kick(g=1.0, dur=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 26) + 46
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 8)
    click = rng.normal(0, 1, n) * np.exp(-t * 240) * 0.22
    return np.tanh((body + click) * 1.6) * g


def clap(g=1.0, dur=0.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = hp(rng.normal(0, 1, n), 1200)
    return np.tanh(noise * np.exp(-t * 22) * 1.3) * g


def hat(g=0.2, dur=0.06, open_=False):
    n = int(dur * SR * (3 if open_ else 1))
    t = np.arange(n) / SR
    return hp(rng.normal(0, 1, n), 6000) * np.exp(-t * (26 if not open_ else 11)) * g


def pluck(f, dur=0.3, g=1.0):
    s = tone(f, dur, "tri") + 0.3 * tone(f * 2.01, dur, "sine")
    return s * env(len(s), 0.003, 0.14) * g


def marimba(f, dur=0.45, g=1.0):
    s = tone(f, dur, "sine") + 0.4 * tone(f * 4, dur, "sine") + 0.2 * tone(f * 9.2, dur, "sine")
    return s * env(len(s), 0.002, 0.12) * g


def bass(f, dur, g=1.0):
    return lp(tone(f, dur, "saw"), 300) * env(int(dur * SR), 0.008, 0.4) * g


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
        s = seg[chunk // 2: chunk // 2 + (hi - lo)]
        out[lo:hi] = s[: hi - lo]
    t = np.arange(n) / SR
    e = np.clip(t / 0.04, 0, 1) * np.clip((dur - t) / (dur * 0.7), 0, 1)
    return out * e * 4 * g


N_ = {"A2": 110.0, "C3": 130.81, "E3": 164.81, "F2": 87.31, "G2": 98.0, "B2": 123.47,
      "D3": 146.83, "A3": 220.0, "C4": 261.63, "E4": 329.63, "F4": 349.23, "G4": 392.0,
      "B3": 246.94, "D4": 293.66, "A4": 440.0, "C5": 523.25, "E5": 659.26}

CHORDS = [("Am", ["A2", "C3", "E3"], ["A4", "C5", "E5"], "A2"),
          ("F", ["F2", "A2", "C3"], ["F4", "A4", "C5"], "F2"),
          ("C", ["C3", "E3", "A3"], ["E4", "A4", "C5"], "C3"),
          ("G", ["G2", "B2", "D3"], ["D4", "G4", "B3"], "G2")]

# ---------------------------------------------------------------- music
nbar = int(math.ceil(DUR / BAR))
prog = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
for bar in range(nbar):
    t0 = bar * BAR
    if t0 >= DUR:
        break
    name, ch, arp, root = CHORDS[prog[bar % len(prog)]]
    add(music, kick(0.85), t0)
    add(music, kick(0.7), t0 + 1.5 * BEAT)
    add(music, kick(0.75), t0 + 2.5 * BEAT)
    add(music, clap(0.42), t0 + BEAT)
    add(music, clap(0.46), t0 + 3 * BEAT)
    for i in range(8):
        add(music, hat(0.14 if i % 2 else 0.2), t0 + i * BEAT / 2)
    add(music, hat(0.16, open_=True), t0 + 3.5 * BEAT)
    add(music, bass(N_[root], 0.4, 0.8), t0)
    add(music, bass(N_[root], 0.3, 0.6), t0 + 1.5 * BEAT)
    add(music, bass(N_[ch[2]], 0.35, 0.5), t0 + 2.5 * BEAT)
    for i in range(8):
        nn = arp[i % len(arp)]
        add(music, marimba(N_[nn] * (2 if i in (3, 7) else 1), 0.4, 0.13), t0 + i * BEAT / 2)

# ---------------------------------------------------------------- sfx
# intro pop + whoosh
add(sfx, kick(0.7, 0.2), 0.02)
add(sfx, sweep(0.45, 500, 6500, 0.4), 0.05)
# shrink pops (three steps of the hook)
for tt, f in ((0.9, 880), (1.35, 1180), (1.8, 1480)):
    add(sfx, tone(f, 0.18, "sine") * env(int(0.18 * SR), 0.002, 0.05) * 0.5, tt)
# scene cuts
for tt in [starts[1], starts[2], starts[3], starts[4], starts[5], starts[6]]:
    add(sfx, sweep(0.22, 2600, 700, 0.28), tt - 0.12)
# crumb lands on the hands + strain
add(sfx, kick(0.9, 0.35), starts[1] + 1.55)
add(sfx, lp(rng.normal(0, 1, int(0.5 * SR)), 180) * env(int(0.5 * SR), 0.02, 0.25) * 1.4, starts[1] + 1.55)
# water: pressure squeak then a deep "solid" thud (surface tension)
add(sfx, tone(320, 0.25, "saw") * env(int(0.25 * SR), 0.01, 0.1) * 0.15, starts[2] + 0.9)
add(sfx, kick(1.0, 0.5), starts[2] + 1.2)
add(sfx, lp(rng.normal(0, 1, int(0.4 * SR)), 260) * env(int(0.4 * SR), 0.005, 0.18) * 1.2, starts[2] + 1.2)
# cold: shimmer + shiver ticks
for i in range(6):
    add(sfx, tone(2200 + i * 180, 0.3, "sine") * env(int(0.3 * SR), 0.01, 0.2) * 0.08, starts[3] + i * 0.06)
add(sfx, sweep(0.5, 7000, 2000, 0.3), starts[3])
# fall whistle + landing
add(sfx, sweep(0.9, 2400, 500, 0.35), starts[4] + 0.35)
add(sfx, tone(1400, 0.9, "sine") * env(int(0.9 * SR), 0.05, 0.6) * 0.12, starts[4] + 0.4)
add(sfx, kick(1.0, 0.4), starts[4] + 1.75)
add(sfx, lp(rng.normal(0, 1, int(0.35 * SR)), 300) * env(int(0.35 * SR), 0.004, 0.12) * 1.1, starts[4] + 1.75)
# ants: tiny ticks
for i in range(10):
    add(sfx, hat(0.05, 0.03), starts[5] + 0.2 + i * 0.25)
# finale chime
for i, f in enumerate((523.25, 659.26, 783.99)):
    add(sfx, tone(f, 1.0, "sine") * env(int(1.0 * SR), 0.01, 0.4) * 0.16, starts[6] + 1.9 + i * 0.08)

# ---------------------------------------------------------------- mix
voice = np.zeros(N, np.float32)
for ln, st in zip(LINES, starts):
    w = wave.open(ln["file"], "rb")
    a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    if w.getnchannels() == 2:
        a = a.reshape(-1, 2).mean(1)
    voice[int(st * SR): int(st * SR) + len(a)] += a[: max(0, N - int(st * SR))] * 1.0

def rms(x):
    return float(np.sqrt((x ** 2).mean()) + 1e-9)


# gain staging by RMS so the voice always sits on top of the bed
music_g = float(S.get("audio.music_rms", 0.026)) / rms(music)
sfx_g = float(S.get("audio.sfx_rms", 0.048)) / rms(sfx)
voice_g = float(S.get("audio.voice_rms", 0.15)) / rms(voice)
print("gains", round(music_g, 3), round(sfx_g, 3), round(voice_g, 3),
      "| stems rms", round(rms(music), 4), round(rms(sfx), 4), round(rms(voice), 4))
mix = music * music_g + sfx * sfx_g + voice * voice_g
mix = np.tanh(mix * 1.15) * 0.93
fi = int(0.06 * SR)
mix[:fi] *= np.linspace(0, 1, fi)
fo = int(0.5 * SR)
mix[-fo:] *= np.linspace(1, 0, fo)
st = np.stack([mix, np.concatenate([np.zeros(180, np.float32), mix[:-180]]) * 0.99], axis=1)
pcm = (np.clip(st, -1, 1) * 32767).astype("<i2")
out_wav = S.get("paths.audio", "audio/mix.wav")
os.makedirs(os.path.dirname(out_wav) or ".", exist_ok=True)
with wave.open(out_wav, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("mix.wav", round(len(mix) / SR, 2), "s | DUR", round(DUR, 2))
