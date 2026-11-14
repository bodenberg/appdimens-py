"""Tkinter: a card whose padding and fonts follow the window size."""
import tkinter as tk

import appdimens as ad
from appdimens.integrations import bind_tk

root = tk.Tk()
root.geometry("360x640")
scope = ad.Dimens()
label = tk.Label(root, text="Hello, AppDimens", bg="#1d4ed8", fg="white")
label.pack(fill="x")


def relayout(_m):
    pad = int(round(scope.sdpPx(16)))
    label.configure(font=("Helvetica", -int(round(scope.asspPx(18)))), padx=pad, pady=pad)


scope.add_listener(relayout)
bind_tk(root, scope)
root.mainloop()
