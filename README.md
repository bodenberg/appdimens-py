<div align="center">

# AppDimens for Python

**Write `16` once. AppDimens makes it the right size on laptops, 4K monitors, ultrawides, tablets, TVs — and in Blender.**

[![Release](https://img.shields.io/badge/release-3.2.0-1d4ed8.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.7%2B%20%7C%20PyPy-15803d.svg)](pyproject.toml)
[![Blender](https://img.shields.io/badge/Blender-2.80%20%E2%86%92%204.x-f59e0b.svg)](docs/BLENDER.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-15803d.svg)](LICENSE)

Part of the [AppDimens family](https://github.com/bodenberg/appdimens) — same token names and the same math as Android, iOS, Flutter, React Native, Web, .NET, GTK, Qt, LVGL, Roku and Games.

🇧🇷 [Resumo em português](#-resumo-em-português)

</div>

---

## Install

```bash
pip install appdimens
```

Zero dependencies, pure Python, CPython 3.7+ (the oldest Python shipped by Blender 2.8x) and PyPy.

## First line of code

```python
import appdimens as ad

ad.update(width=411, height=914, density=2.625)   # or one of the adapters below

ad.sdp(16)      # 21.92  — spacing that follows the smallest side
ad.ssp(14)      # text, follows the user's font scale
ad.asdp(16)     # "auto": linear on phones, gentle on tablets/TVs/monitors
ad.sdpPx(16)    # physical pixels (× density)
ad.dimen("16asdp")  # string form for themes / config files (cached)
```

Every family token is available: `hdp`, `wdp`, `hsp`, `wsp`, `sem` (text that ignores font scale), the strategy
prefixes (`a` auto, `p` percent, `pw` power, `f` fluid, `i` interpolated, `log`, `dg` diagonal, `pr` perimeter,
`ft` fit, `fl` fill, `d` density), the flags `a` (aspect ratio), `i` (ignore multi-window), `ia`, the inverters
`Ph`/`Lh`/`Pw`/`Lw` and `Px`. Grammar: `<prefix><s|h|w><dp|sp|em>[Px][a|i|ia][Ph|Lh|Pw|Lw][a|i|ia][Px]`.

## Scopes (one per window)

```python
from appdimens import Dimens, DimenMetrics

win = Dimens(DimenMetrics(width=1280, height=800, density=1.5))
win.sdp(16); win.asspPx(18); win.hdpLw(40)
win.add_listener(lambda m: relayout())   # called on every real change (no-op updates are ignored)
```

A scope publishes one immutable tuple per update, so reads are lock-free and thread-safe.

## Adapters

| Toolkit | Snapshot | Live binding |
|---------|----------|--------------|
| Tkinter | `metrics_from_tk(root)` | `bind_tk(root, scope)` |
| PySide6 / PySide2 / PyQt6 / PyQt5 | `metrics_from_qt(widget_or_screen)` | call in `resizeEvent` / `screenChanged` |
| Kivy | `metrics_from_kivy(Window)` | `bind_kivy(scope)` |
| pygame / pygame-ce | `metrics_from_pygame(surface)` | on `VIDEORESIZE` |
| pyglet / arcade | `metrics_from_pyglet(window)` | on `on_resize` |
| wxPython | `metrics_from_wx(frame)` | on `EVT_SIZE` / `EVT_DPI_CHANGED` |
| Dear PyGui | `metrics_from_dearpygui()` | viewport resize callback |
| Panda3D / Ursina | `metrics_from_panda3d(base)` | `window-event` |
| Blender | `integrations.blender.metrics_from_region(region)` / `metrics_from_render(scene)` | `RegionScopes().get(region)` |
| Anything else | `metrics_from_pixels(w_px, h_px, density)` | — |

All adapters are duck-typed: importing `appdimens.integrations` never imports a GUI toolkit.

## Blender

`blender/appdimens_blender` is an add-on (Blender 2.80+) and Extension (4.2+). Build the zip with the library vendored:

```bash
python scripts/build_blender_addon.py   # → dist/appdimens_blender-3.2.0.zip
```

It adds a **Sidebar ▸ AppDimens** panel (live calculator, render-relative values, **Fit Text to Render** operator
that rescales text objects from a reference resolution to the current output — 1080p → 4K → 9:16) and an
importable API for other add-ons:

```python
from appdimens_blender import region_dimens, render_dimens
d = region_dimens(context.region)        # follows Resolution Scale + monitor DPI
blf.size(0, d.sspPx(13))
text_obj.data.size = render_dimens(scene).asdp(0.12)
```

Details: [docs/BLENDER.md](docs/BLENDER.md).

## Custom strategies

Your own scaling rule, shared with every AppDimens platform (same JSON document and text formulas):

```python
from appdimens import custom as c
hud = c.scaling_formula("base * pow(sw / 360, 0.8)")
c.load_scaling_strategies(open("custom-strategies.json").read())
c.cdp(16, hud); c.csp(14, "brand"); c.cdp_px(24, "brand")
```

Details: [docs/CUSTOM.md](docs/CUSTOM.md).

## Also included

- `appdimens.units` — `mm`, `cm`, `inch` → dp / px / sp using the snapshot DPI.
- `appdimens.resize` — `auto_resize_text(text, w, h, measure)`: largest font size that fits, O(log n) measurements.
- Facilitators — `scope.rotate`, `scope.mode` (TV, car, watch, foldables…), `scope.qualifier`, `scope.screen`.
- Percent space — `space_w(50)`, `space_h(10)`, `space_sw(25)`.
- `resolve(value, strategy=…, aspect_ratio=True, k=0.01)` — custom aspect-ratio sensitivity.

## Precision and performance

- **Parity:** `tests/test_parity.py` checks all 12 strategies × 11 axis variants × 4 flag combos on 20 screens
  (phones, foldables, tablets, 4K, 5K ultrawide, watches, multi-window) against vectors generated from the
  reference implementation — equal to `1e-12`.
- **Speed (CPython 3.13, x86-64):** ~85 ns per `sdp(16)` (one tuple read + one multiply; the rest is the Python call
  itself), ~230 ns for cached `dimen("16asdp")`, ~4 µs to publish a new snapshot with all 528 factors.
  Run `python scripts/bench.py`.

## Docs

[Integrations](docs/INTEGRATIONS.md) · [Custom strategies](docs/CUSTOM.md) · [Blender](docs/BLENDER.md) · [Theory (hub)](https://github.com/bodenberg/appdimens/blob/main/DOCS/THEORY.md) · [AI skill](skills/appdimens-py/SKILL.md) · [LLMS.txt](LLMS.txt) · [Changelog](CHANGELOG.md)

---

<!-- appdimens-family:begin (maintained in bodenberg/appdimens tools/family_block.py) -->
## 🌍 AppDimens family

Same token names and the same math on every platform — [hub](https://github.com/bodenberg/appdimens) · [AI agent skills](https://github.com/bodenberg/appdimens-skills) · [custom strategies](https://github.com/bodenberg/appdimens/blob/main/DOCS/CUSTOM.md) (one JSON for every platform).

| Platform | Library | Scaled `16` |
|---|---|---|
| Android — Jetpack Compose, Views, Java | [appdimens-dynamic](https://github.com/bodenberg/appdimens-dynamic) | `16.sdp` · `16.sdp(context)` |
| Android — XML resources | [appdimens-sdps](https://github.com/bodenberg/appdimens-sdps) | `@dimen/_16sdp` |
| Android — XML text sizes | [appdimens-ssps](https://github.com/bodenberg/appdimens-ssps) | `@dimen/_16ssp` |
| Kotlin / Compose Multiplatform | [appdimens-kmp](https://github.com/bodenberg/appdimens-kmp) | `16.sdp` |
| iOS · macOS — SwiftUI, UIKit, AppKit, Metal | [appdimens-ios](https://github.com/bodenberg/appdimens-ios) | `16.sdp` |
| Flutter | [appdimens-flutter](https://github.com/bodenberg/appdimens-flutter) | `16.sdp` |
| React Native / Expo | [appdimens-react-native](https://github.com/bodenberg/appdimens-react-native) | `sdp(16)` |
| Web — HTML/CSS, React, Vue, Svelte, Angular | [appdimens-web](https://github.com/bodenberg/appdimens-web) | `sdp(16)` · `16sdp` |
| .NET — MAUI, WPF, WinForms, WinUI, Android | [appdimens-net-binding](https://github.com/bodenberg/appdimens-net-binding) | `16.Sdp()` · `{sdp:16}` |
| Qt 5/6 — QML, Widgets | [appdimens-qt](https://github.com/bodenberg/appdimens-qt) | `AppDimens.sdp(16)` · `16_sdp` |
| GTK 3/4 and portable C99 | [appdimens-gtk](https://github.com/bodenberg/appdimens-gtk) | `16sdp` (CSS) · `ad_sdp(&m, 16)` |
| LVGL 8/9 — MCUs, embedded Linux | [appdimens-lvgl](https://github.com/bodenberg/appdimens-lvgl) | `lv_ad_sdp(16)` |
| Roku — BrightScript / SceneGraph | [appdimens-roku](https://github.com/bodenberg/appdimens-roku) | `ad.sdp(16)` |
| Python — Tkinter, Qt, Kivy, pygame, Blender | **appdimens-py** (this repository) | `ad.sdp(16)` |
| Games — Unity, Unreal, Godot, C/C++, .NET, Android | [appdimens-games](https://github.com/bodenberg/appdimens-games) | `64f.ASdp()` · `AppDimens.asdp(64)` · `appdimens::asdp(64)` |

<!-- appdimens-family:end -->

## 🇧🇷 Resumo em português

**AppDimens para Python** ajusta tamanhos (espaçamentos, fontes, ícones) ao tamanho da janela e à densidade da tela.
Instale com `pip install appdimens`, troque `16` por `ad.sdp(16)` e `14` (texto) por `ad.ssp(14)`. Funciona com
Tkinter, Qt (PySide/PyQt), Kivy, pygame, pyglet, wxPython, Dear PyGui, Panda3D e **Blender** (add-on incluído, 2.80 →
4.x, com painel, operador para ajustar textos à resolução de render e API para outros add-ons). Mesmos nomes e
mesma matemática de toda a família AppDimens.

## Author

**Jean Bodenberg** — [@bodenberg](https://github.com/bodenberg) · Apache 2.0
