import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def find_latest_css():
    root = BASE_DIR
    fns = [
        os.path.join(root, entry)
        for root, dirs, files in os.walk(root)
        for entry in dirs + files
        if entry.endswith(".css")
    ]

    substring_list = ["static/fontawesome", "static/ckeditor", "static/admin"]
    fns = [f for f in fns if not any(map(f.__contains__, substring_list))]

    t = [os.path.getmtime(f) for f in fns]

    if len(t):
        t = max(t)
    else:
        t = os.path.getmtime(os.path.join(root, "project/settings.py"))

    return int(t)
