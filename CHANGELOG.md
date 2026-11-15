# Changelog

## Unreleased

- `appdimens.custom`: custom scaling strategies, a port of `appdimens-dynamic` library-custom — factor
  lambdas (`custom_scale_strategy`), code/text formulas (`scaling_formula`), full configurations with
  rules per device / size / orientation / multi-window, the shared JSON document (`load_scaling_strategies`,
  `export_scaling_strategies`), built-ins and presets; `cdp`, `cdp_px`, `csp`, `csp_px`, `csp_units`.
  Reproduces the cross-platform 540-case fixture.

## 3.2.0 — first release

- Pure-Python port of AppDimens 3.2: 12 strategies, 11 axis variants (`s`/`h`/`w` + inverters), flags `a`/`i`/`ia`,
  kinds `dp`/`sp`/`em`, `Px`, custom aspect-ratio sensitivity, percent space, facilitators.
- `Dimens` scopes with lock-free immutable state and change listeners; module-level tokens via PEP 562.
- String expressions with bounded cache: `dimen("16asdp")`, `"10spaceW"`, `"5mm"`, `"3px"`.
- `units` (mm/cm/inch ↔ dp/px/sp) and `resize` (O(log n) auto-resize text).
- Adapters: Tkinter, Qt for Python, Kivy, pygame, pyglet/arcade, wxPython, Dear PyGui, Panda3D, Blender.
- Blender add-on/Extension (2.80 → 4.x) with panel, render-relative text operator and API.
- Parity tests against vectors generated from the reference implementation (1e-12).
