"""Synthesize the episode narration.

Usage:
    python tools/make_voice.py episodes/<slug>/lines.txt [--engine edge|piper] [--voice ru-RU-DmitryNeural]

Writes voice/line_XX.wav + voice/lines.json (id, text, file, dur) — the engine and the
audio mixer both build the timeline from that file, so re-running with another voice
re-times the whole episode.
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import settings as S  # noqa: E402


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def to_wav(src, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ac", "2", "-ar", "44100", dst], check=True)
    return duration(dst)


def piper_line(text, dst):
    piper = S.get("voice.piper_bin")
    model = S.get("voice.piper_model")
    subprocess.run([piper, "-m", model, "-f", dst], input=text.encode("utf-8"),
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return duration(dst)


async def edge_line(text, dst, voice, rate, retries):
    import edge_tts

    proxy = S.get("voice.proxy")
    if proxy:
        os.environ.setdefault("HTTP_PROXY", proxy)
        os.environ.setdefault("HTTPS_PROXY", proxy)
    for k in range(retries):
        try:
            await edge_tts.Communicate(text, voice, rate=rate).save(dst)
        except Exception as e:
            print(f"    retry {k}: {type(e).__name__}")
        if os.path.exists(dst) and os.path.getsize(dst) > 4000 and duration(dst) > 0.4:
            return duration(dst)
        await asyncio.sleep(1.0 + 1.5 * k)
    raise RuntimeError("no audio received: " + text[:40])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines", help="txt file, one narration line per line")
    ap.add_argument("--engine", default=S.get("voice.engine", "edge"), choices=["edge", "piper"])
    ap.add_argument("--voice", default=S.get("voice.voice", "ru-RU-DmitryNeural"))
    ap.add_argument("--rate", default=S.get("voice.rate", "+30%"))
    ap.add_argument("--out", default=S.get("paths.voice_dir", "voice"))
    args = ap.parse_args()

    lines = [ln.strip() for ln in open(args.lines, encoding="utf-8") if ln.strip()]
    os.makedirs(args.out, exist_ok=True)
    meta = []
    for i, text in enumerate(lines):
        wav = os.path.join(args.out, f"line_{i:02d}.wav")
        if args.engine == "piper":
            d = piper_line(text, wav)
        else:
            mp3 = os.path.join(args.out, f"line_{i:02d}.mp3")
            d = asyncio.run(edge_line(text, mp3, args.voice, args.rate,
                                      int(S.get("voice.retries", 6))))
            d = to_wav(mp3, wav)
            os.remove(mp3)
        meta.append({"id": i, "text": text, "file": wav, "dur": round(d, 3)})
        print(f"{i}: {d:5.2f}s  {text[:50]}")
    json.dump(meta, open(os.path.join(args.out, "lines.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"speech total {sum(m['dur'] for m in meta):.2f}s -> {args.out}/lines.json")


if __name__ == "__main__":
    main()
