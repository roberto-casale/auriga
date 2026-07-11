"""Validatore statico dei contenuti: mappe, trigger, eventi, riferimenti.

Uso (da auriga/):  ../.venv/bin/python tools/validate.py
Esce con codice 1 se trova errori.
"""
import os
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from game.enemies import BATTLES, ENEMIES  # noqa: E402
from game.items import ITEMS  # noqa: E402
from game.skills import LEARN, SKILLS  # noqa: E402
from game.stats import PARTY_DEFS  # noqa: E402
from game.story import CAST, DIALOGUES, EVENTS  # noqa: E402
from world.mapdata import LEGEND, MAPS  # noqa: E402

errors = []
warnings = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


# --------------------------------------------------------------- mappe
def map_grid(data):
    rows = data["rows"]
    w = max(len(r) for r in rows)
    return [r.ljust(w, "#") for r in rows], w, len(rows)


def solid_at(rows, legend, x, y):
    if not (0 <= y < len(rows) and 0 <= x < len(rows[0])):
        return True
    spec = legend.get(rows[y][x], LEGEND["#"])
    return spec.get("solid", False)


def bfs(rows, legend, start, npc_cells):
    w, h = len(rows[0]), len(rows)
    seen = set()
    q = deque([start])
    while q:
        x, y = q.popleft()
        if (x, y) in seen or solid_at(rows, legend, x, y) or (x, y) in npc_cells:
            continue
        seen.add((x, y))
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            q.append((x + dx, y + dy))
    return seen


ENTRY = {"habitat": [(5, 6), (33, 16)],
         "officina": [(1, 10), (34, 18)],
         "idroponica": [(3, 2), (38, 12)],
         "cuore": [(1, 2)]}

for mid, data in MAPS.items():
    rows, w, h = map_grid(data)
    legend = dict(LEGEND)
    legend.update(data.get("legend", {}))
    for y, row in enumerate(rows):
        for ch in row:
            if ch not in legend:
                err(f"{mid}: carattere sconosciuto {ch!r} alla riga {y}")
    for x in range(w):
        if not solid_at(rows, legend, x, 0) and not any(
                t.get("transfer") and (t["x"], t["y"]) == (x, 0)
                for t in data["triggers"]):
            warn(f"{mid}: bordo superiore aperto in ({x},0)")

    npc_cells = {(e["x"], e["y"]) for e in data.get("entities", [])}
    reach = set()
    for start in ENTRY.get(mid, []):
        if solid_at(rows, legend, *start):
            err(f"{mid}: ingresso {start} non calpestabile")
        reach |= bfs(rows, legend, start, npc_cells)

    for e in data.get("entities", []):
        if solid_at(rows, legend, e["x"], e["y"]):
            err(f"{mid}: NPC {e['name']} su cella solida ({e['x']},{e['y']})")
        if e.get("event") and e["event"] not in EVENTS:
            err(f"{mid}: NPC {e['name']} evento inesistente {e['event']}")
        adj = any((e["x"] + dx, e["y"] + dy) in reach
                  for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)))
        if not adj:
            err(f"{mid}: NPC {e['name']} non raggiungibile ({e['x']},{e['y']})")

    ids = set()
    for t in data.get("triggers", []):
        tid = t["id"]
        if tid in ids:
            err(f"{mid}: trigger id duplicato {tid}")
        ids.add(tid)
        x, y = t["x"], t["y"]
        ch = rows[y][x] if (0 <= y < h and 0 <= x < w) else "#"
        solid = solid_at(rows, legend, x, y)
        if t.get("on") == "enter":
            if solid:
                err(f"{mid}: trigger enter {tid} su cella solida ({x},{y}) [{ch!r}]")
            elif (x, y) not in reach:
                err(f"{mid}: trigger enter {tid} non raggiungibile ({x},{y})")
        else:  # interact: la cella o una adiacente deve essere raggiungibile
            spots = [(x, y)] if not solid and (x, y) in reach else [
                (x + dx, y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                if (x + dx, y + dy) in reach]
            if not spots:
                err(f"{mid}: trigger interact {tid} non raggiungibile ({x},{y})")
        if "event" in t and t["event"] not in EVENTS:
            err(f"{mid}: trigger {tid} evento inesistente {t['event']}")
        if "battle" in t and t["battle"] not in BATTLES:
            err(f"{mid}: trigger {tid} battaglia inesistente {t['battle']}")
        if "chest" in t:
            if t["chest"][0] not in ITEMS:
                err(f"{mid}: trigger {tid} oggetto inesistente {t['chest'][0]}")
            if not t.get("once"):
                err(f"{mid}: chest {tid} senza once=True")
        if "transfer" in t:
            dest, dx_, dy_, fc = t["transfer"]
            if dest not in MAPS:
                err(f"{mid}: transfer {tid} mappa inesistente {dest}")
            else:
                drows, dw, dh = map_grid(MAPS[dest])
                dlegend = dict(LEGEND)
                dlegend.update(MAPS[dest].get("legend", {}))
                if solid_at(drows, dlegend, dx_, dy_):
                    err(f"{mid}: transfer {tid} arrivo su cella solida "
                        f"({dx_},{dy_}) in {dest}")
                for t2 in MAPS[dest]["triggers"]:
                    if (t2["x"], t2["y"]) == (dx_, dy_) and "transfer" in t2:
                        err(f"{mid}: transfer {tid} atterra su un altro "
                            f"transfer in {dest} → loop!")
            if fc not in ("up", "down", "left", "right"):
                err(f"{mid}: transfer {tid} facing non valido {fc}")
    for a in data.get("auto", []):
        if a["event"] not in EVENTS:
            err(f"{mid}: auto-evento inesistente {a['event']}")

# --------------------------------------------------------------- storia
VALID_EVENT_ACTIONS = {"dialogue", "battle", "give", "flag", "affinity",
                       "heal", "sfx", "music", "act", "checkpoint",
                       "if_flag", "transfer", "ending"}
VALID_STEPS = {"say", "choice", "flag", "affinity", "join", "give", "sfx"}


def check_actions(eid, actions):
    for a in actions:
        kind = a[0]
        if kind not in VALID_EVENT_ACTIONS:
            err(f"evento {eid}: azione sconosciuta {kind}")
        elif kind == "dialogue" and a[1] not in DIALOGUES:
            err(f"evento {eid}: dialogo inesistente {a[1]}")
        elif kind == "battle" and a[1] not in BATTLES:
            err(f"evento {eid}: battaglia inesistente {a[1]}")
        elif kind == "give" and a[1] not in ITEMS:
            err(f"evento {eid}: oggetto inesistente {a[1]}")
        elif kind == "if_flag":
            check_actions(eid, a[2])
            check_actions(eid, a[3])
        elif kind == "transfer" and a[1] not in MAPS:
            err(f"evento {eid}: transfer verso mappa inesistente {a[1]}")


for eid, actions in EVENTS.items():
    check_actions(eid, actions)


def check_steps(did, steps):
    for s in steps:
        kind = s[0]
        if kind not in VALID_STEPS:
            err(f"dialogo {did}: step sconosciuto {kind}")
        elif kind == "say":
            if s[1] not in CAST:
                err(f"dialogo {did}: personaggio sconosciuto {s[1]!r}")
            if not isinstance(s[2], str) or not s[2]:
                err(f"dialogo {did}: testo mancante")
        elif kind == "choice":
            for label, branch in s[1]:
                check_steps(did, branch)
        elif kind == "join" and s[1] not in PARTY_DEFS:
            err(f"dialogo {did}: join di membro inesistente {s[1]}")
        elif kind == "give" and s[1] not in ITEMS:
            err(f"dialogo {did}: oggetto inesistente {s[1]}")


for did, steps in DIALOGUES.items():
    check_steps(did, steps)

# ------------------------------------------------------- battaglie/skill
for bid, b in BATTLES.items():
    for ek in b["enemies"]:
        if ek not in ENEMIES:
            err(f"battaglia {bid}: nemico inesistente {ek}")

for key, table in LEARN.items():
    if key not in PARTY_DEFS:
        err(f"LEARN: personaggio inesistente {key}")
    for lv, sids in table.items():
        for sid in sids:
            if sid not in SKILLS:
                err(f"LEARN {key}: skill inesistente {sid}")

for ek, e in ENEMIES.items():
    for mv in e["moves"]:
        if mv["kind"] not in ("attack", "attack_all", "debuff"):
            err(f"nemico {ek}: mossa kind sconosciuto {mv['kind']}")

# ---------------------------------------------- catena di progressione
chain_flags = []
for eid in ("ev_ilan_join", "ev_sette_join", "ev_imboscata_spore",
            "ev_glifo_idro", "ev_rovine_intro", "ev_sentinella", "ev_altare"):
    if eid not in EVENTS:
        err(f"catena principale: manca l'evento {eid}")

# flag richiesti dai transfer devono essere impostabili da qualche parte
all_set_flags = set()


def collect_flags(seq):
    for a in seq:
        if a[0] == "flag":
            all_set_flags.add(a[1])
        elif a[0] == "if_flag":
            collect_flags(a[2])
            collect_flags(a[3])
        elif a[0] == "choice":
            for label, branch in a[1]:
                collect_flags(branch)


for actions in EVENTS.values():
    collect_flags(actions)
for steps in DIALOGUES.values():
    collect_flags(steps)

for mid, data in MAPS.items():
    for t in data.get("triggers", []):
        req = t.get("requires_flag")
        if req and req not in all_set_flags:
            err(f"{mid}: trigger {t['id']} richiede flag mai impostato {req!r}")

# ------------------------------------------------------------- risultato
print(f"Controlli completati: {len(errors)} errori, {len(warnings)} avvisi")
for w in warnings:
    print("  AVVISO:", w)
for e in errors:
    print("  ERRORE:", e)
sys.exit(1 if errors else 0)
