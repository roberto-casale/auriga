"""Test del percorso 'sconfitta a metà evento': non deve mai bloccare la quest.

Scenario: il party perde la battaglia scriptata di Sette in officina.
Atteso: si respawna al checkpoint, l'NPC Sette è ANCORA presente e ritentando
si ottiene la chiave magnetica.

Uso (da auriga/):  ../.venv/bin/python tools/test_defeat_event.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from game.party import new_game_state  # noqa: E402
from main import Game  # noqa: E402
from scenes.battle import BattleScene  # noqa: E402
from scenes.dialogue import DialogueScene  # noqa: E402
from scenes.explore import ExploreScene  # noqa: E402

game = Game()
DT = 1 / 30


def frames(n):
    for _ in range(n):
        game.step(DT, [])


def press(key, settle=2):
    game.step(DT, [pygame.event.Event(pygame.KEYDOWN, key=key)])
    frames(settle)


def drain_dialogues(limit=300):
    for _ in range(limit):
        sc = game.scenes.current
        if isinstance(sc, DialogueScene):
            press(pygame.K_SPACE)
        elif isinstance(sc, BattleScene):
            return sc
        else:
            frames(2)
            if not isinstance(game.scenes.current, (DialogueScene, BattleScene)):
                return None
    raise SystemExit("dialoghi infiniti")


# stato: in officina, davanti al pod di Sette, checkpoint lì accanto
st = new_game_state()
st.add_member("ilan")
st.set_flag("ilan_joined", True)
st.set_flag("hab_door_open", True)
st.done.add("habitat_intro")
st.done.add("off_intro")
st.map_id, st.px, st.py, st.facing = "officina", 18, 7, "up"
st.checkpoint = ("officina", 4, 17)
game.state = st
game.scenes.clear_to(ExploreScene(game))
frames(10)

# indebolisci il party e parla con Sette (dialogo → battaglia)
for m in st.members:
    m.hp = 1
    m.en = 0
press(pygame.K_SPACE)          # interagisci col pod
battle = drain_dialogues()
assert isinstance(battle, BattleScene), "la battaglia di Sette non è partita"
assert battle.can_flee is False, "b_officina deve essere non fuggibile"

# perdi: difenditi finché non arriva la sconfitta
for _ in range(4000):
    sc = game.scenes.current
    if not isinstance(sc, BattleScene):
        break
    if sc.phase == "menu":
        press(pygame.K_DOWN); press(pygame.K_DOWN); press(pygame.K_DOWN)
        press(pygame.K_SPACE, settle=3)    # Difendi
    else:
        frames(4)
drain_dialogues()               # messaggio di respawn
frames(5)

explore = game.scenes.current
assert isinstance(explore, ExploreScene), type(explore).__name__
assert st.map_id == "officina" and (st.px, st.py) == (4, 17), \
    f"respawn sbagliato: {st.map_id} {(st.px, st.py)}"
assert not st.flag("sette_joined"), "il flag NON deve essere impostato dopo la sconfitta"
assert any(n.name == "Sette" and n.active(st) for n in explore.npcs), \
    "SOFT-LOCK: l'NPC Sette è sparito dopo la sconfitta!"
assert not st.has_item("chiave_magnetica")
print("OK sconfitta: evento interrotto, NPC ancora presente, niente chiave")

# riprova e vinci: cura il party e livella per sicurezza
for m in st.members:
    m.base["atk"] += 40
    m.hp, m.en = m.max_hp, m.max_en

# torna dal pod e ritenta
st.px, st.py = 18, 7
explore.load_map("officina", 18, 7, "up")
frames(10)
press(pygame.K_SPACE)
battle = drain_dialogues()
assert isinstance(battle, BattleScene), "il retry non ha fatto ripartire la battaglia"
for _ in range(6000):
    sc = game.scenes.current
    if not isinstance(sc, BattleScene):
        break
    if sc.phase == "menu":
        press(pygame.K_SPACE, settle=2)    # Attacca
    elif sc.phase in ("target_enemy", "victory", "intro"):
        press(pygame.K_SPACE, settle=3)
    else:
        frames(4)
drain_dialogues()
frames(5)
assert st.flag("sette_joined") and st.has_member("sette")
assert st.has_item("chiave_magnetica") and st.flag("ascensore_aperto"), \
    "la chiave non è arrivata al retry"
print("OK retry: Sette nel party, chiave magnetica ottenuta")
print("TEST SCONFITTA-DURANTE-EVENTO SUPERATO ✔")
