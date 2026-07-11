"""Playthrough automatico COMPLETO: dal titolo ai titoli di coda.

Guida il gioco headless attraverso l'intera storia usando gli stessi percorsi
di input del giocatore (eventi tastiera + pathfinding sul tilemap), verificando
una serie di traguardi. Salva uno screenshot per traguardo.

Uso (da auriga/):
  ../.venv/bin/python tools/playthrough.py [cartella_screenshot]
"""
import os
import sys
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from game.skills import SKILLS  # noqa: E402
from main import Game  # noqa: E402
from scenes.battle import BattleScene  # noqa: E402
from scenes.dialogue import DialogueScene  # noqa: E402
from scenes.ending import EndingScene  # noqa: E402
from scenes.explore import ExploreScene  # noqa: E402
from scenes.menu import PauseMenuScene, SaveMenuScene  # noqa: E402
from scenes.title import TitleScene  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else None
DT = 1 / 30
game = Game()
fail = []
shot_i = 0
total_frames = 0


# ------------------------------------------------------------- primitive
def frames(n=1):
    global total_frames
    for _ in range(n):
        game.step(DT, [])
        total_frames += 1
        if total_frames > 400_000:
            raise SystemExit("TIMEOUT globale: il test è in stallo")


def press(key, settle=2):
    global total_frames
    game.step(DT, [pygame.event.Event(pygame.KEYDOWN, key=key)])
    total_frames += 1
    frames(settle)


def top():
    return game.scenes.current


def shot(name):
    global shot_i
    if OUT:
        os.makedirs(OUT, exist_ok=True)
        shot_i += 1
        pygame.image.save(game.screen,
                          os.path.join(OUT, f"{shot_i:02d}_{name}.png"))


def milestone(name, cond, detail=""):
    mark = "OK " if cond else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))
    if not cond:
        fail.append(name)
    shot(name)


# ------------------------------------------------------ dialoghi/battaglie
def advance_dialogue(choices=None, limit=400):
    choices = list(choices or [])
    for _ in range(limit):
        sc = top()
        if not isinstance(sc, DialogueScene):
            frames(2)
            return choices
        if sc.choice_menu is not None and sc.shown >= len(sc.text):
            want = choices.pop(0) if choices else 0
            n = len(sc.choice_menu.items)
            delta = (want - sc.choice_menu.index) % n
            for _ in range(delta):
                press(pygame.K_DOWN)
            press(pygame.K_SPACE)
        else:
            press(pygame.K_SPACE)
    raise SystemExit("dialogo senza fine?")


def _menu_select(scene, want_index):
    n = len(scene.menu.items)
    delta = (want_index - scene.menu.index) % n
    for _ in range(delta):
        press(pygame.K_DOWN)
    press(pygame.K_SPACE)


def battle_auto(policy="mixed", limit=6000):
    """Gioca la battaglia in corso. policy: mixed | attack | guard."""
    for _ in range(limit):
        sc = top()
        if not isinstance(sc, BattleScene):
            frames(2)
            return
        ph = sc.phase
        if ph in ("intro", "victory"):
            press(pygame.K_SPACE, settle=3)
        elif ph == "anim":
            frames(4)
        elif ph == "defeat":
            frames(6)
        elif ph == "menu":
            if policy == "guard":
                _menu_select(sc, 3)
                continue
            actor = sc.actor
            hurt = [m for m in sc.alive_party() if m.hp < m.max_hp * 0.45]
            heal_sid = next(
                (sid for sid in actor.skills
                 if SKILLS[sid]["kind"] in ("heal", "heal_all")
                 and not SKILLS[sid].get("self_only")
                 and actor.en >= SKILLS[sid]["cost"]), None)
            atk_sid = next(
                (sid for sid in actor.skills
                 if SKILLS[sid]["kind"] in ("attack", "attack_all")
                 and actor.en >= SKILLS[sid]["cost"] * 2), None)
            if policy == "mixed" and hurt and heal_sid:
                sc._pending_test = ("skill", heal_sid, hurt[0])
                _menu_select(sc, 1)
            elif policy == "mixed" and atk_sid:
                sc._pending_test = ("skill", atk_sid, None)
                _menu_select(sc, 1)
            else:
                sc._pending_test = None
                _menu_select(sc, 0)          # Attacca
        elif ph == "skill":
            want = getattr(sc, "_pending_test", None)
            sid = want[1] if want else sc.menu.items[0][1]
            idx = next((i for i, (_, v) in enumerate(sc.menu.items)
                        if v == sid and sc.menu.enabled[i]), None)
            if idx is None:
                press(pygame.K_ESCAPE)       # nessuna skill pagabile
                sc._pending_test = None
                _menu_select(sc, 0)
            else:
                _menu_select(sc, idx)
        elif ph == "target_enemy":
            press(pygame.K_SPACE, settle=3)
        elif ph == "target_ally":
            want = getattr(sc, "_pending_test", None)
            desired = want[2] if want and want[2] is not None else None
            if desired is not None:
                for _ in range(6):
                    targets = sc.alive_party()
                    if targets[sc.target_i % len(targets)] is desired:
                        break
                    press(pygame.K_RIGHT)
            press(pygame.K_SPACE, settle=3)
        else:
            frames(2)
    raise SystemExit("battaglia senza fine?")


# ------------------------------------------------------------ navigazione
def _walkable(tm, x, y, goal, npcs):
    if (x, y) == goal:
        return not tm.spec(x, y).get("solid", False)
    if tm.spec(x, y).get("solid", False):
        return False
    if (x, y) in npcs:
        return False
    tr = tm.triggers.get((x, y))
    if tr and "transfer" in tr:              # niente porte se non richieste
        return False
    return True


def path_to(goal):
    sc = top()
    tm = sc.tilemap
    npcs = {(n.x, n.y) for n in sc.active_npcs()}
    start = (sc.player.x, sc.player.y)
    if start == goal:
        return []
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt not in prev and _walkable(tm, nxt[0], nxt[1], goal, npcs):
                prev[nxt] = cur
                q.append(nxt)
    if goal not in prev:
        raise SystemExit(f"nessun percorso verso {goal} in {sc.game.state.map_id}"
                         f" da {start}")
    path = [goal]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])
    return list(reversed(path))[1:]


def go(x, y, choices=None, policy="mixed", limit=3000):
    """Cammina fino alla cella (x,y), gestendo dialoghi/battaglie incontrati."""
    choices = list(choices or [])
    start_map = game.state.map_id
    for _ in range(limit):
        sc = top()
        if isinstance(sc, DialogueScene):
            choices = advance_dialogue(choices)
            continue
        if isinstance(sc, BattleScene):
            battle_auto(policy)
            continue
        if isinstance(sc, SaveMenuScene):
            press(pygame.K_ESCAPE)
            continue
        if isinstance(sc, ExploreScene):
            if game.state.map_id != start_map:
                return choices                # transfer avvenuto
            if (sc.player.x, sc.player.y) == (x, y) and not sc.player.moving:
                game.auto_dir = None
                return choices
            step = path_to((x, y))
            if not step:
                game.auto_dir = None
                return choices
            nx, ny = step[0]
            game.auto_dir = (nx - sc.player.x, ny - sc.player.y)
            tgt = (nx, ny)
            for _ in range(40):
                frames(1)
                if ((sc.player.x, sc.player.y) == tgt
                        and not sc.player.moving) or top() is not sc:
                    break
            game.auto_dir = None
            continue
        raise SystemExit(f"scena inattesa durante go(): {type(sc).__name__}")
    raise SystemExit(f"go({x},{y}) non converge")


def face(direction):
    """Orienta il personaggio senza muoverlo (verso una cella solida)."""
    sc = top()
    game.auto_dir = {"up": (0, -1), "down": (0, 1),
                     "left": (-1, 0), "right": (1, 0)}[direction]
    frames(2)
    game.auto_dir = None
    frames(1)
    # se la cella era calpestabile il passo parte comunque: attendi l'arrivo
    for _ in range(40):
        if not sc.player.moving:
            break
        frames(1)


def interact(choices=None, policy="mixed"):
    press(pygame.K_SPACE)
    out = list(choices or [])
    for _ in range(600):
        sc = top()
        if isinstance(sc, DialogueScene):
            out = advance_dialogue(out)
        elif isinstance(sc, BattleScene):
            battle_auto(policy)
        elif isinstance(sc, ExploreScene):
            if not sc.actions and sc.waiting is None:
                frames(2)
                return
            frames(2)
        else:
            return                          # es. SaveMenuScene: gestita dal chiamante
    raise SystemExit("interazione senza fine")


st = None

# ================================================================ TEST ==
print("=== PLAYTHROUGH AURIGA ===")

# --- titolo → nuova partita
frames(10)
milestone("titolo", isinstance(top(), TitleScene))
press(pygame.K_SPACE)
frames(20)
advance_dialogue()
st = game.state
milestone("intro_completata",
          isinstance(top(), ExploreScene) and st.map_id == "habitat"
          and len(st.members) == 1)

# --- Ada cura il party (NPC + heal)
go(12, 4)
face("up")
interact()
milestone("ada_cura", st.members[0].hp == st.members[0].max_hp)

# --- baule cabina
go(2, 4)
face("up")
interact()
milestone("baule_habitat", st.inventory.get("razione", 0) >= 5,
          f"razioni={st.inventory.get('razione')}")

# --- terminale col diario
go(31, 3)
face("up")
interact()
milestone("diario", st.has_item("diario_capitano"))

# --- Luce (dialogo secondario)
go(28, 5)
face("up")
interact()

# --- Ilan: dialogo (scelta 1) + battaglia tutorial + porta aperta
go(25, 14)
face("up")
interact(choices=[0])
milestone("ilan_nel_party", st.has_member("ilan") and st.flag("ilan_joined"))
milestone("porta_aperta", st.flag("hab_door_open"))
milestone("exp_guadagnata", st.members[0].exp > 0 or st.members[0].level > 1)

# --- salvataggio al checkpoint (slot 1)
go(3, 10)
press(pygame.K_SPACE)      # savepoint → menu slot
frames(5)
assert isinstance(top(), SaveMenuScene), "il savepoint non apre il menu di salvataggio"
press(pygame.K_SPACE)      # slot 1
frames(5)
press(pygame.K_ESCAPE)
frames(5)
milestone("salvataggio_slot1",
          os.path.isfile(os.path.join(os.path.dirname(__file__), "..",
                                      "saves", "slot1.json")))

# --- anomalia opzionale (battaglia libera) e passaggio in officina
go(10, 19)
frames(10)
if isinstance(top(), BattleScene):
    battle_auto()
milestone("anomalia_habitat", "hab_anomalia" in st.done)
go(34, 16)                 # porta → officina
frames(20)
advance_dialogue()
milestone("arrivo_officina", st.map_id == "officina")

# --- Bruno, poi Sette: join + battaglia + chiave
go(8, 9)
face("up")
interact()
go(18, 7)
face("up")
interact(choices=[0])
milestone("sette_nel_party", st.has_member("sette") and st.flag("sette_joined"))
milestone("chiave_magnetica", st.has_item("chiave_magnetica")
          and st.flag("ascensore_aperto"))

# --- baule officina + anomalia
go(35, 4)
face("up")
interact()
milestone("baule_officina", st.inventory.get("gel", 0) >= 2)
go(28, 12)
frames(10)
if isinstance(top(), BattleScene):
    battle_auto()

# --- ascensore → idroponica
go(35, 18)
frames(20)
advance_dialogue()
milestone("arrivo_idroponica", st.map_id == "idroponica"
          and st.act.startswith("Atto II"))

# --- flirt alla finestra (Kaira/Ilan, scelta romantica)
go(19, 1)
face("up")
interact(choices=[0])
milestone("flirt_finestra", st.affinity.get("kaira_ilan", 0) >= 3,
          f"kaira_ilan={st.affinity.get('kaira_ilan')}")

# --- imboscata al varco: spore + arrivo di Naia
go(19, 10)                 # attraversa il varco (19,9)
frames(10)
advance_dialogue()
milestone("naia_nel_party", st.has_member("naia") and len(st.members) == 4)

# --- flirt all'Albero-Lume (Naia/Sette)
go(18, 12)
face("up")
interact(choices=[0])
milestone("flirt_albero", st.affinity.get("naia_sette", 0) >= 3,
          f"naia_sette={st.affinity.get('naia_sette')}")

# --- terminale glifo → Custode + porta est
go(5, 15)
face("up")
interact()
milestone("glifo_idroponica", st.flag("idro_glifo"))

# --- bauli idroponica
go(37, 3)
face("up")
interact()
go(37, 22)
face("up")
interact()
milestone("bauli_idro", st.has_item("stimolante") and st.has_item("fiala_luce"))

# --- porta est → Cuore
go(39, 12)
frames(20)
advance_dialogue()
milestone("arrivo_cuore", st.map_id == "cuore" and st.act.startswith("Atto III"))

# --- tre glifi + sentinella
go(8, 8)
frames(5)
advance_dialogue()
go(34, 6)
frames(5)
advance_dialogue()
milestone("glifi_1_3", st.flag("cuore_g1") and st.flag("cuore_g3"))
go(21, 12, policy="mixed")   # attraversa il varco: parte la Sentinella a (21,11)
frames(10)
advance_dialogue()
milestone("sentinella_sconfitta", "cuore_sentinella" in st.done)
go(20, 16)
frames(5)
advance_dialogue()
milestone("glifo_2", st.flag("cuore_g2"))

# --- livelli cresciuti nel viaggio
milestone("crescita_livelli", all(m.level >= 3 for m in st.members),
          "livelli=" + ",".join(str(m.level) for m in st.members))

# --- salvataggio pre-boss (slot 2)
go(21, 20)
press(pygame.K_SPACE)
frames(5)
assert isinstance(top(), SaveMenuScene)
press(pygame.K_DOWN)       # slot 2
press(pygame.K_SPACE)
frames(5)
press(pygame.K_ESCAPE)
frames(5)
milestone("salvataggio_slot2",
          os.path.isfile(os.path.join(os.path.dirname(__file__), "..",
                                      "saves", "slot2.json")))

# --- menu di pausa: zaino (usa una razione) e stato
press(pygame.K_ESCAPE)
frames(5)
assert isinstance(top(), PauseMenuScene)
_menu_pause = top()
press(pygame.K_DOWN)       # Stato
press(pygame.K_SPACE)
frames(5)
shot("stato")
press(pygame.K_ESCAPE)     # chiudi stato
press(pygame.K_DOWN)       # Zaino
press(pygame.K_SPACE)
frames(5)
if _menu_pause.mode == "items":
    press(pygame.K_SPACE)  # primo oggetto
    frames(3)
    if _menu_pause.mode == "items_target":
        press(pygame.K_SPACE)
        frames(3)
    press(pygame.K_ESCAPE)
press(pygame.K_ESCAPE)
frames(5)
milestone("menu_pausa", isinstance(top(), ExploreScene))

# --- boss: altare → Custode → scelta finale → epilogo
go(20, 23)
face("up")
interact(choices=[0], policy="mixed")
frames(30)
milestone("finale_raggiunto", isinstance(top(), EndingScene)
          and st.flag("finale_liberato"))

# --- epilogo a scorrimento → titolo (controlla PRIMA di premere: un solo
#     SPACE di troppo sul titolo avvierebbe una nuova partita)
for _ in range(80):
    if isinstance(top(), TitleScene):
        break
    press(pygame.K_SPACE, settle=4)
frames(5)
milestone("ritorno_al_titolo", isinstance(top(), TitleScene))

# --- caricamento slot 2 dal titolo
press(pygame.K_DOWN)       # Carica partita
press(pygame.K_SPACE)
frames(5)
assert isinstance(top(), SaveMenuScene)
press(pygame.K_DOWN)       # slot 2
press(pygame.K_SPACE)
frames(20)
st = game.state
milestone("caricamento_slot2", isinstance(top(), ExploreScene)
          and st.map_id == "cuore" and len(st.members) == 4
          and st.flag("cuore_g1"))

# --- percorso di sconfitta: hp a 1, battaglia in guardia → respawn
explore = top()
for m in st.members:
    m.hp = 1
    m.en = 0
explore.waiting = "battle"
game.scenes.push(BattleScene(game, "b_rovine2"))
frames(5)
battle_auto(policy="guard")
advance_dialogue()
milestone("respawn_da_sconfitta",
          st.map_id == st.checkpoint[0]
          and all(m.hp == max(1, int(m.max_hp * 0.5)) for m in st.members),
          f"mappa={st.map_id} hp={[m.hp for m in st.members]}")

# ------------------------------------------------------------- riepilogo
print()
print(f"Frame simulati: {total_frames}  (~{total_frames / 30 / 60:.1f} minuti di gioco)")
print(f"Livelli finali: {[f'{m.name} Lv.{m.level}' for m in st.members]}")
print(f"Affinità: {st.affinity}")
if fail:
    print(f"\nRISULTATO: {len(fail)} TRAGUARDI FALLITI → {fail}")
    sys.exit(1)
print("\nRISULTATO: PLAYTHROUGH COMPLETO SENZA ERRORI ✔")
