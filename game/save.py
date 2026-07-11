"""Salvataggio/caricamento su file JSON in ./saves/ (3 slot).

Nel browser (pygbag) il filesystem è quello virtuale di emscripten: la scrittura
diretta funziona, mentre il rename atomico può non essere disponibile — per
questo `save_slot` ripiega su una scrittura diretta se `os.replace` fallisce.
"""
import json
import os
import sys

from game.party import GameState
from settings import SAVES_DIR, SAVE_SLOTS, VERSION

_IS_WEB = sys.platform == "emscripten"


def _slot_path(n):
    return os.path.join(SAVES_DIR, f"slot{n}.json")


def save_slot(n, state):
    os.makedirs(SAVES_DIR, exist_ok=True)
    data = {"version": VERSION, "state": state.to_dict()}
    path = _slot_path(n)
    if _IS_WEB:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        return True
    tmp = path + ".tmp"                     # nativo: scrittura atomica
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    try:
        os.replace(tmp, path)
    except OSError:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
    return True


def load_slot(n):
    try:
        with open(_slot_path(n), encoding="utf-8") as fh:
            data = json.load(fh)
        return GameState.from_dict(data["state"])
    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def slot_info(n):
    """Riassunto per la schermata di caricamento, o None se vuoto/corrotto."""
    try:
        with open(_slot_path(n), encoding="utf-8") as fh:
            data = json.load(fh)
        st = data["state"]
        mins = int(st.get("playtime", 0) // 60)
        names = [m["key"].capitalize() for m in st.get("members", [])]
        top = max([m.get("level", 1) for m in st.get("members", [])], default=1)
        return {
            "act": st.get("act", "?"),
            "time": f"{mins // 60}h {mins % 60:02d}m",
            "party": ", ".join(names),
            "level": top,
        }
    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        return None


def all_slots():
    return {n: slot_info(n) for n in range(1, SAVE_SLOTS + 1)}
