# Настройки

Все ручки живут в `settings.json` в корне; читаются через `settings.py` (модуль `S.get("раздел.ключ")`).
Переопределить файл целиком можно переменной окружения `VIDEO_MULT_SETTINGS=/path/to/settings.json`.

## video

| Ключ | По умолчанию | Что делает |
|---|---|---|
| `width`, `height` | 1080 × 1920 | Размер кадра. Вертикаль 9:16 — Reels/Shorts/TikTok |
| `fps` | 30 | Частота кадров; 24 для «медленного» вида, 30 для динамики |
| `supersample` | 1.5 | Во сколько раз рисуем крупнее и потом уменьшаем (сглаживание). 1.5 — компромисс; 2.0 заметно медленнее |
| `workers` | 3 | Процессов рендера. На 4 ядрах больше 3 не ставить: `multiprocessing.Pool` на Windows падает |
| `crf` | 18 | Качество H.264: меньше — лучше и тяжелее |
| `preset` | medium | Скорость энкода x264 |

## timeline

| Ключ | По умолчанию | Что делает |
|---|---|---|
| `gap` | 0.26 | Пауза между репликами, сек. Больше — спокойнее монтаж |
| `min_duration` | 25.0 | Минимальная длина ролика |
| `tail` | 2.0 | Сколько секунд оставить после последней реплики (эндкард) |

Итоговая длина = `max(min_duration, конец_речи + tail)`; сцены режутся от `voice/lines.json`.

## voice

| Ключ | По умолчанию | Что делает |
|---|---|---|
| `engine` | `edge` | `edge` (нейросетевой Microsoft) или `piper` (офлайн) |
| `voice` | `ru-RU-DmitryNeural` | Голос Edge: `ru-RU-DmitryNeural` (муж.), `ru-RU-SvetlanaNeural` (жен.) |
| `rate` | `+30%` | Темп речи. 25–35 % — «реилс-темп»; выше 40 % звучит неразборчиво |
| `proxy` | `http://127.0.0.1:10809` | HTTP-прокси для Edge TTS (в РФ без него `NoAudioReceived`) |
| `piper_bin`, `piper_model` | пути Windows | Офлайн-фолбэк |
| `retries` | 6 | Повторы на `NoAudioReceived` с бэкоффом |

## audio

| Ключ | По умолчанию | Что делает |
|---|---|---|
| `voice_rms` | 0.15 | Целевая громкость голоса (RMS). Ниже — голос тонет |
| `music_rms` | 0.026 | Целевая громкость музыки; ~ −12 дБ от голоса |
| `sfx_rms` | 0.048 | Целевая громкость шумов (удары, whoosh) |
| `bpm` | 96 | Темп музыки; от него же считаются акценты SFX |
| `lufs` | −14 | Интегральная громкость финала (так делают платформы) |
| `true_peak` | −1.5 | Пиковый уровень в dBTP |
| `lra` | 9 | Диапазон громкости для loudnorm |

## palette

Цвета в RGB-массивах: `ink`, `cream`, `cream_d`, `floor`, `coral`, `mustard`, `teal`, `teal_d`,
`sky`, `white`, `blue`, `sand`, `green`. Меняются без правки кода — стиль серии задаётся здесь.

## fonts

| Ключ | По умолчанию |
|---|---|
| `bold` | `C:/Windows/Fonts/segoeuib.ttf` |
| `regular` | `C:/Windows/Fonts/segoeui.ttf` |

Нужен шрифт с кириллицей. На Linux — `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`.

## paths

| Ключ | По умолчанию | Что делает |
|---|---|---|
| `voice_dir` | `voice` | Куда `make_voice.py` кладёт wav + `lines.json` |
| `frames_dir` | `frames` | Кадры PNG `f0000.png…` |
| `audio` | `audio/mix.wav` | Сведённый звук |
| `out` | `out.mp4` | Готовый ролик |
