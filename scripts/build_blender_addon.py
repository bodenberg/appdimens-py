"""Builds dist/appdimens_blender-<ver>.zip with the appdimens package vendored.

Usage: python scripts/build_blender_addon.py
Install: Blender ▸ Edit ▸ Preferences ▸ Add-ons (or Get Extensions ▸ Install from Disk).
"""
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import appdimens  # noqa: E402

out_dir = os.path.join(ROOT, "dist")
os.makedirs(out_dir, exist_ok=True)
zpath = os.path.join(out_dir, "appdimens_blender-%s.zip" % appdimens.VERSION)
addon = os.path.join(ROOT, "blender", "appdimens_blender")
pkg = os.path.join(ROOT, "src", "appdimens")

with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _dirs, files in os.walk(addon):
        if "__pycache__" in base or os.sep + "vendor" in base:
            continue
        for f in files:
            full = os.path.join(base, f)
            z.write(full, os.path.join("appdimens_blender", os.path.relpath(full, addon)))
    z.writestr("appdimens_blender/vendor/__init__.py", "")
    for base, _dirs, files in os.walk(pkg):
        if "__pycache__" in base:
            continue
        for f in files:
            if f.endswith(".py"):
                full = os.path.join(base, f)
                z.write(full, os.path.join("appdimens_blender", "vendor", "appdimens", os.path.relpath(full, pkg)))
print(zpath)
