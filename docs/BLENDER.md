# AppDimens in Blender

Supported: Blender **2.80 → 4.1** as a legacy add-on (`bl_info`) and **4.2+** as an Extension
(`blender_manifest.toml`). The library is pure Python 3.7+, so it runs on every Python Blender has shipped since 2.80.

## Install

1. `python scripts/build_blender_addon.py` → `dist/appdimens_blender-3.2.0.zip` (library vendored in `vendor/`).
2. Blender ▸ *Edit ▸ Preferences ▸ Add-ons ▸ Install…* (4.2+: *Get Extensions ▸ ⌄ ▸ Install from Disk*).
3. Enable **AppDimens**. The panel lives in *3D Viewport ▸ Sidebar (N) ▸ AppDimens*.

## Two coordinate systems

| Use | Snapshot | Logical unit | Density |
|-----|----------|--------------|---------|
| Add-on UI, `blf`, `gpu` overlays, gizmos | `metrics_from_region(region)` | Blender UI unit (`px / ui_scale`) | `preferences.system.ui_scale` (Resolution Scale × monitor DPI × pixel size) |
| Render burn-ins, title text, compositor overlays | `metrics_from_render(scene)` | output pixel (with `resolution_percentage` and pixel aspect) | 1 |

### UI drawing

```python
import blf
from appdimens_blender import region_dimens

def draw():
    d = region_dimens(bpy.context.region)   # cached per region; updates only on change
    blf.size(0, d.sspPx(13))                # version-safe wrapper: appdimens.integrations.blender.blf_size
    blf.position(0, d.sdpPx(12), d.sdpPx(12), 0)
    blf.draw(0, "Hello")
```

`layout.scale_y = layout_scale(d, 1.0, "asdp")` grows button rows calmly on large regions.

### Render-relative text

Design at a reference resolution (default 1920 × 1080), then deliver anywhere:

```python
from appdimens_blender import render_dimens
r = render_dimens(scene)        # e.g. 3840×2160, or 1080×1920 for vertical video
text.data.size = r.asdp(0.12)
```

The **Fit Text to Render** operator does this for the selected text objects: it multiplies `data.size` by
`factor(current render) / factor(reference)` for the chosen strategy. Use `ftsdp` (fit) to never overflow when the
aspect ratio changes (16:9 → 9:16), `flsdp` (fill) to always cover, `asdp` for the calm default.

## API reference

`appdimens.integrations.blender`: `ui_scale`, `metrics_from_region`, `metrics_from_render`, `scope_for_region`,
`scope_for_render`, `blf_size`, `layout_scale`, `RegionScopes`.

`appdimens_blender`: `region_dimens(region)`, `render_dimens(scene)`, `register()`, `unregister()`.

## Testing without Blender

`tests/test_blender_addon.py` runs the add-on register/unregister cycle and helpers against a fake `bpy`.
CI also installs the real `bpy` wheel (Python 3.11) and registers the add-on.
