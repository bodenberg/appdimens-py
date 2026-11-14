# Integrations

All adapters live in `appdimens.integrations` and are duck-typed (no toolkit import at module load).
Logical unit = the unit the toolkit lays out in; `density` = physical pixels per logical unit.

| Toolkit | Logical unit | Density source | Call |
|---------|--------------|----------------|------|
| Tkinter | physical px ÷ (dpi/96) | `tk scaling × 72 / 96` | `bind_tk(root, scope)` |
| Qt for Python | Qt logical px | `QScreen.devicePixelRatio()`; DPI `physicalDotsPerInch()` | `metrics_from_qt(widget)` in `resizeEvent` and on `QWindow.screenChanged` |
| Kivy | px ÷ `Metrics.density` | `kivy.metrics.Metrics.density`, `fontscale` | `bind_kivy(scope)` |
| pygame / pygame-ce | px | pass `drawable / window` when HiDPI | `metrics_from_pygame(surface, density)` |
| pyglet / arcade | window size (logical) | `get_pixel_ratio()` | `metrics_from_pyglet(window)` in `on_resize` |
| wxPython | DIP (`ToDIP`) | `GetDPIScaleFactor()` | `metrics_from_wx(frame)` on `EVT_SIZE`/`EVT_DPI_CHANGED` |
| Dear PyGui | viewport px | pass yours | `metrics_from_dearpygui()` |
| Panda3D / Ursina | `base.win` px | pass yours | `metrics_from_panda3d(base)` |
| Blender | UI unit / output px | `preferences.system.ui_scale` / 1 | see [BLENDER.md](BLENDER.md) |

## Games written in Python

Use `ftsdp` (fit) for HUD elements that must never be cropped on ultrawide or portrait screens, `flsdp` (fill) for
backgrounds that must always cover, `asdp` for menus. For engine-level features (letterbox viewports, world ↔ screen,
safe areas, upscalers) see [appdimens-games](https://github.com/bodenberg/appdimens-games), whose C API can be called
through `ctypes`/`cffi`.
