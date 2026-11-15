---
name: appdimens-py
description: Use for responsive sizing in Python apps and tools — Tkinter, PySide/PyQt, Kivy, pygame, pyglet/arcade, wxPython, Dear PyGui, Panda3D/Ursina and Blender add-ons/render text — and whenever the user mentions appdimens (Python), `pip install appdimens`, sdp/ssp/asdp tokens in Python, `ad.dimen("16sdp")`, or porting Android dp/sp sizes to a Python GUI.
---

# appdimens (Python) — workflow

**Library:** `appdimens` 3.2.0 (PyPI), pure Python 3.7+, zero deps. Same names and math as the whole AppDimens family.

## Core idea
`sdp(16) = 16 × smallestSide / 300` logical units. `hdp`/`wdp` use height/width. `ssp` = text × user font scale;
`sem` = text without it. `Px` suffix = × density (physical pixels). Prefixes pick the strategy: `a` auto (phone + big
screens, recommended for desktop), `ft` fit / `fl` fill (games, canvases), `p` percent, `pw` power, `f` fluid,
`log`, `dg`, `pr`, `i`, `d`. Flags: `a` aspect ratio, `i` ignore multi-window. Inverters: `Ph Lh Pw Lw`.

## Steps
1. **Build a snapshot from the toolkit** (never hard-code sizes):
   Tk `metrics_from_tk/bind_tk`, Qt `metrics_from_qt(widget)` in `resizeEvent`, Kivy `bind_kivy`, pygame
   `metrics_from_pygame(surface)` on `VIDEORESIZE`, pyglet `metrics_from_pyglet`, wx `metrics_from_wx`,
   Blender `metrics_from_region` (UI) / `metrics_from_render` (output), else `metrics_from_pixels(w_px, h_px, density)`.
2. **One `Dimens` scope per window** (`scope = ad.Dimens(m)`), or the module default (`ad.update(...)`, `ad.sdp`).
3. **Replace literals:** padding/margins → `sdp`; text → `ssp` (or `assp` on desktop/TV); toolkits that take
   physical pixels (pygame, Pillow, `blf`, wx on Windows) → the `Px` form (`sdpPx`, `sspPx`).
4. **Re-layout on change:** `scope.add_listener(cb)`; updates that do not change the snapshot are ignored.
5. **Validate:** at 300 × 533 density 1 every token returns its input; check a 1080p and a 4K/ultrawide size.

## Blender
Install the zip from `scripts/build_blender_addon.py`. In add-on code:
`from appdimens_blender import region_dimens, render_dimens`; `blf_size(0, region_dimens(region).sspPx(13))`;
render text: `obj.data.size = render_dimens(scene).asdp(0.12)` (use `ftsdp` when the delivery aspect changes).

## Custom strategies

Only when the project declares `customStrategies` (or the user asks for their own rule):
`from appdimens import custom as c` → `c.load_scaling_strategies(text)` once, then `c.cdp(16, "id")`,
`c.csp(14, "id")`; one-off math: `c.scaling_formula("base * pow(sw / 360, 0.8)")` or
`c.custom_scale_strategy(lambda s: s.clamp(s.width / 360, 0.85, 1.8))`. Never invent ids.

## Don'ts
- Don't multiply by density twice (Qt/pyglet sizes are already logical; pygame/Pillow are physical).
- Don't parse strings in tight loops if you can keep the resolver: `f = scope.fn("asdp")` then `f(16)`.
- Don't use obsolete names (`balanced`, `fx`, `dy`, `fitsdp`, `fillsdp`).
