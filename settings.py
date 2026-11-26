"""Settings loader for VIDEO_MULT. Reads settings.json once; every module uses CFG."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULTS = {
    "video": {"width": 1080, "height": 1920, "fps": 30, "supersample": 1.5,
              "workers": 3, "crf": 18, "preset": "medium"},
    "timeline": {"gap": 0.26, "min_duration": 25.0, "tail": 2.0},
    "voice": {"engine": "edge", "voice": "ru-RU-DmitryNeural", "rate": "+30%",
              "proxy": "http://127.0.0.1:10809",
              "piper_bin": "C:/Users/Ali PC/.local/bin/piper.exe",
              "piper_model": "C:/Users/Ali PC/chalkboard/piper-models/ru_RU-dmitri-medium.onnx",
              "retries": 6},
    "audio": {"voice_rms": 0.15, "music_rms": 0.026, "sfx_rms": 0.048, "bpm": 96,
              "lufs": -14.0, "true_peak": -1.5, "lra": 9},
    "palette": {},
    "fonts": {"bold": "C:/Windows/Fonts/segoeuib.ttf", "regular": "C:/Windows/Fonts/segoeui.ttf"},
    "paths": {"voice_dir": "voice", "frames_dir": "frames", "audio": "audio/mix.wav", "out": "out.mp4"},
}


def _merge(base, extra):
    out = dict(base)
    for k, v in (extra or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load(path=None):
    path = path or os.environ.get("VIDEO_MULT_SETTINGS") or os.path.join(HERE, "settings.json")
    try:
        with open(path, encoding="utf-8") as f:
            return _merge(DEFAULTS, json.load(f))
    except FileNotFoundError:
        return dict(DEFAULTS)


CFG = load()


def get(dotted, default=None):
    node = CFG
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node


def rgb(key):
    v = CFG.get("palette", {}).get(key)
    return tuple(v) if v else None
