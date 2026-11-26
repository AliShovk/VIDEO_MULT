"""Encode rendered frames, mux the soundtrack, build chat previews.

Usage:
    python tools/build.py [--frames frames] [--audio audio/mix.wav] [--out out.mp4]
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import settings as S  # noqa: E402


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default=S.get("paths.frames_dir", "frames"))
    ap.add_argument("--audio", default=S.get("paths.audio", "audio/mix.wav"))
    ap.add_argument("--out", default=S.get("paths.out", "out.mp4"))
    args = ap.parse_args()

    fps = int(S.get("video.fps", 30))
    crf = str(S.get("video.crf", 18))
    preset = S.get("video.preset", "medium")
    lufs = float(S.get("audio.lufs", -14.0))
    tp = float(S.get("audio.true_peak", -1.5))
    lra = float(S.get("audio.lra", 9))

    n = len([f for f in os.listdir(args.frames) if f.startswith("f")])
    dur = round(n / fps, 3)
    print(f"frames: {n} -> {dur}s")
    raw = os.path.join(os.path.dirname(args.out) or ".", "out_raw.mp4")

    run(["ffmpeg", "-y", "-framerate", str(fps), "-i", os.path.join(args.frames, "f%04d.png"),
         "-i", args.audio, "-c:v", "libx264", "-preset", preset, "-crf", crf,
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
         "-movflags", "+faststart", raw])
    run(["ffmpeg", "-y", "-i", raw, "-c:v", "copy",
         "-af", f"loudnorm=I={lufs}:TP={tp}:LRA={lra}", "-c:a", "aac", "-b:a", "192k",
         "-t", str(dur), args.out])

    gif = os.path.join(os.path.dirname(args.out) or ".", "preview_loop.gif")
    run(["ffmpeg", "-y", "-i", args.out, "-t", "5", "-vf",
         "fps=12,scale=300:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer",
         gif])
    sheet = os.path.join(os.path.dirname(args.out) or ".", "contact_sheet.jpg")
    run(["ffmpeg", "-y", "-i", args.out, "-vf",
         "select='eq(n\\,25)+eq(n\\,80)+eq(n\\,190)+eq(n\\,275)+eq(n\\,350)+eq(n\\,430)+eq(n\\,520)+eq(n\\,730)',"
         "scale=270:-1,tile=4x2:padding=6:color=0x1a1a1c", "-frames:v", "1", "-update", "1", sheet])
    subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size:stream=width,height,nb_frames", "-of", "default=nw=1", args.out])


if __name__ == "__main__":
    main()
