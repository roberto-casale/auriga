"""Esplorazione: movimento a griglia, trigger, NPC, eventi della storia."""
import pygame

from asset_loader import assets
from core import text as T
from core import ui
from core.audio import audio
from core.scene import Scene
from game.items import ITEMS
from game.story import EVENTS
from scenes.battle import BattleScene
from scenes.dialogue import DialogueScene
from scenes.menu import PauseMenuScene, SaveMenuScene
from settings import (C_ACCENT, C_TEXT, C_TEXT_DIM, DEFEAT_HP_FRAC, HEIGHT,
                      KEYS_CONFIRM, KEY_MENU, KEYS_DOWN, KEYS_LEFT,
                      KEYS_RIGHT, KEYS_UP, TILE, WIDTH)
from world.entities import NPC, Entity
from world.tilemap import Camera, TileMap


class ExploreScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.actions = []              # coda azioni dell'evento in corso
        self.consume_id = None         # trigger da marcare 'done' a fine evento
        self.waiting = None            # "dialogue" | "battle" | None
        self.banner_t = 99.0
        self.player = None
        self.load_map(game.state.map_id, game.state.px, game.state.py,
                      game.state.facing, first=True)

    # ------------------------------------------------------------- mappa
    def load_map(self, map_id, x, y, facing, first=False):
        st = self.game.state
        st.map_id = map_id
        st.px, st.py = x, y
        st.facing = facing
        self.tilemap = TileMap(map_id, st)
        leader = st.members[0].key if st.members else "kaira"
        self.player = Entity(leader, x, y, facing)
        self.npcs = [NPC(spec) for spec in self.tilemap.data.get("entities", [])]
        w, h = self.tilemap.pixel_size
        self.camera = Camera(w, h)
        self.camera.follow(self.player.px * TILE, self.player.py * TILE)
        self.banner_t = 0.0
        self._banner_surf = None
        self.prev_cell = (x, y)
        audio.play_music(self.tilemap.data.get("music", "explore"))
        # gli auto-eventi partono al primo update(): durante il costruttore la
        # scena non è ancora nello stack e un push verrebbe perso
        self._auto_pending = True

    def _run_auto(self):
        st = self.game.state
        for auto in self.tilemap.data.get("auto", []):
            if auto.get("once") and auto["id"] in st.done:
                continue
            req = auto.get("requires_flag")
            if req and not st.flag(req):
                continue
            self.run_event(auto["event"],
                           auto["id"] if auto.get("once") else None)
            return

    def active_npcs(self):
        return [n for n in self.npcs if n.active(self.game.state)]

    # ----------------------------------------------------------- eventi
    def run_event(self, event_id, consume_id=None):
        self.actions = list(EVENTS[event_id])
        self.consume_id = consume_id
        self.process_actions()

    def process_actions(self):
        st = self.game.state
        while self.actions:
            act = self.actions.pop(0)
            kind = act[0]
            if kind == "dialogue":
                from game.story import DIALOGUES
                self.waiting = "dialogue"
                self.game.scenes.push(DialogueScene(self.game, DIALOGUES[act[1]]))
                return
            if kind == "battle":
                self.waiting = "battle"
                self.game.scenes.push(BattleScene(self.game, act[1]))
                return
            if kind == "give":
                st.add_item(act[1], act[2])
            elif kind == "flag":
                st.set_flag(act[1], act[2])
            elif kind == "affinity":
                st.affinity[act[1]] = st.affinity.get(act[1], 0) + act[2]
            elif kind == "heal":
                st.full_heal()
            elif kind == "sfx":
                audio.sfx(act[1])
            elif kind == "music":
                audio.play_music(act[1])
            elif kind == "act":
                st.act = act[1]
            elif kind == "checkpoint":
                st.checkpoint = (st.map_id, self.player.x, self.player.y)
            elif kind == "if_flag":
                branch = act[2] if st.flag(act[1]) else act[3]
                self.actions = list(branch) + self.actions
            elif kind == "transfer":
                self.load_map(act[1], act[2], act[3], act[4])
            elif kind == "ending":
                from scenes.ending import EndingScene
                self.actions = []
                self.consume_id = None
                self.game.scenes.clear_to(EndingScene(self.game))
                return
        if self.consume_id:
            st.done.add(self.consume_id)
            self.consume_id = None

    def on_resume(self, result=None):
        st = self.game.state
        if self.waiting == "battle":
            self.waiting = None
            if result == "defeat":
                self.respawn()
                return
            if result == "flee":
                # l'evento si interrompe: il trigger resta armato
                self.actions = []
                self.consume_id = None
                audio.play_music(self.tilemap.data.get("music", "explore"))
                return
            audio.play_music(self.tilemap.data.get("music", "explore"))
            self.process_actions()
            return
        if self.waiting == "dialogue":
            self.waiting = None
            self.process_actions()

    def respawn(self):
        st = self.game.state
        for m in st.members:
            m.hp = max(1, int(m.max_hp * DEFEAT_HP_FRAC))
            m.en = m.max_en // 2
            m.buffs = []
            m.guarding = False
        self.actions = []
        self.consume_id = None
        map_id, x, y = st.checkpoint
        self.load_map(map_id, x, y, "down")
        self.game.scenes.push(DialogueScene(self.game, [
            ("say", "", "La squadra ripiega e riprende fiato all'ultimo "
                        "checkpoint. Nessuno viene lasciato indietro: "
                        "si riparte, più prudenti di prima."),
        ]))
        self.waiting = "dialogue"

    # ------------------------------------------------------------ trigger
    def step_on(self, x, y):
        st = self.game.state
        tr = self.tilemap.trigger_at(x, y)
        if tr is None or tr.get("on") != "enter":
            return
        if tr.get("unless_flag") and st.flag(tr["unless_flag"]):
            return
        if "transfer" in tr:
            req = tr.get("requires_flag")
            if req and not st.flag(req):
                px, py = self.prev_cell
                self.player.x, self.player.y = px, py
                self.player.px, self.player.py = float(px), float(py)
                if tr.get("locked_event"):
                    self.run_event(tr["locked_event"])
                return
            m, tx, ty, fc = tr["transfer"]
            audio.sfx("door")
            self.load_map(m, tx, ty, fc)
            return
        if "battle" in tr:
            self.waiting = "battle"
            self.consume_id = tr["id"] if tr.get("once") else None
            self.game.scenes.push(BattleScene(self.game, tr["battle"]))
            return
        if "event" in tr:
            self.run_event(tr["event"], tr["id"] if tr.get("once") else None)

    def interact(self):
        st = self.game.state
        # 1. NPC nella cella di fronte
        fx, fy = self.player.facing_cell()
        for npc in self.active_npcs():
            if (npc.x, npc.y) == (fx, fy):
                npc.face_towards(self.player.x, self.player.y)
                if npc.event:
                    self.run_event(npc.event)
                return
        # 2. trigger sulla cella corrente, poi su quella di fronte
        for cx, cy in ((self.player.x, self.player.y), (fx, fy)):
            tr = self.tilemap.trigger_at(cx, cy)
            if tr is None or tr.get("on") != "interact":
                continue
            if "savepoint" in tr:
                st.full_heal()
                st.checkpoint = (st.map_id, self.player.x, self.player.y)
                audio.sfx("save")
                self.game.scenes.push(SaveMenuScene(self.game, "save"))
                return
            if "chest" in tr:
                item_id, qty = tr["chest"]
                st.add_item(item_id, qty)
                st.done.add(tr["id"])
                audio.sfx("item")
                name = ITEMS[item_id]["name"]
                extra = f" x{qty}" if qty > 1 else ""
                self.waiting = "dialogue"
                self.game.scenes.push(DialogueScene(self.game, [
                    ("say", "", f"Trovato: {name}{extra}!")]))
                return
            if "event" in tr:
                self.run_event(tr["event"], tr["id"] if tr.get("once") else None)
                return

    def _facing_interactable(self):
        fx, fy = self.player.facing_cell()
        for npc in self.active_npcs():
            if (npc.x, npc.y) == (fx, fy):
                return "Parla"
        for cx, cy in ((self.player.x, self.player.y), (fx, fy)):
            tr = self.tilemap.trigger_at(cx, cy)
            if tr is not None and tr.get("on") == "interact":
                return "Esamina"
        return None

    # ------------------------------------------------------------- input
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key == KEY_MENU:
            self.game.scenes.push(PauseMenuScene(self.game))
            return
        if event.key in KEYS_CONFIRM and not self.player.moving:
            self.interact()

    def update(self, dt):
        st = self.game.state
        st.playtime += dt
        if self._auto_pending and self.waiting is None and not self.actions:
            self._auto_pending = False
            self._run_auto()
            return
        was_moving = self.player.moving
        if not self.player.moving:
            keys = pygame.key.get_pressed()
            d = getattr(self.game, "auto_dir", None)   # hook per i test
            if d is None:
                if any(keys[k] for k in KEYS_UP):
                    d = (0, -1)
                elif any(keys[k] for k in KEYS_DOWN):
                    d = (0, 1)
                elif any(keys[k] for k in KEYS_LEFT):
                    d = (-1, 0)
                elif any(keys[k] for k in KEYS_RIGHT):
                    d = (1, 0)
            if d is not None:
                self.prev_cell = (self.player.x, self.player.y)
                self.player.try_move(d[0], d[1], self.tilemap,
                                     self.active_npcs())
        self.player.update(dt)
        for npc in self.npcs:
            npc.update(dt)
        st.px, st.py, st.facing = self.player.x, self.player.y, self.player.facing
        self.camera.follow(self.player.px * TILE + TILE // 2,
                           self.player.py * TILE + TILE // 2)
        self.banner_t += dt
        # trigger d'ingresso quando il passo si completa
        if was_moving and not self.player.moving:
            self.step_on(self.player.x, self.player.y)

    # -------------------------------------------------------------- draw
    def draw(self, surface):
        surface.fill((6, 8, 14))
        self.tilemap.draw(surface, self.camera)
        drawables = [self.player] + self.active_npcs()
        for ent in sorted(drawables, key=lambda e: e.draw_order):
            ent.draw(surface, self.camera)
        # nome della zona (in dissolvenza all'ingresso); il banner è composto
        # UNA volta su una superficie propria: mai set_alpha sui pannelli cachati
        if self.banner_t < 3.0:
            if self._banner_surf is None:
                name = self.tilemap.data.get("name", "")
                w = assets.font("title", 30).size(name)[0] + 60
                b = pygame.Surface((w, 56), pygame.SRCALPHA)
                b.blit(ui.panel(w, 56), (0, 0))
                b.blit(assets.font("title", 30).render(name, True, C_TEXT),
                       (30, 10))
                self._banner_surf = b
            alpha = 255 if self.banner_t < 2.2 else int(255 * (3.0 - self.banner_t) / 0.8)
            self._banner_surf.set_alpha(alpha)
            surface.blit(self._banner_surf, (24, 20))
        # suggerimento interazione
        hint = self._facing_interactable()
        if hint and not self.player.moving:
            w = assets.font("text", 20).size(hint)[0] + 92
            surface.blit(ui.panel(w, 40), ((WIDTH - w) // 2, HEIGHT - 56))
            T.draw(surface, f"SPAZIO  {hint}", (WIDTH // 2, HEIGHT - 48), 20,
                   C_ACCENT, align="center")
