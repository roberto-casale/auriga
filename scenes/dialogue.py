"""Scena di dialogo (overlay): typewriter, ritratti, scelte, effetti."""
import pygame

from asset_loader import assets
from core import text as T
from core import ui
from core.audio import audio
from core.scene import Scene
from game.story import CAST
from settings import (C_ACCENT, C_ACCENT2, C_TEXT, C_TEXT_DIM, HEIGHT,
                      KEYS_CONFIRM, WIDTH)

CPS = 80                      # caratteri al secondo
BOX_W, BOX_H = 1180, 178
BOX_X, BOX_Y = (WIDTH - BOX_W) // 2, HEIGHT - BOX_H - 26
PORTRAIT = 264


class DialogueScene(Scene):
    overlay = True

    def __init__(self, game, steps):
        super().__init__(game)
        self.queue = list(steps)
        self.speaker = ""
        self.text = ""
        self.lines = []
        self.shown = 0.0
        self.choice_menu = None
        self.done = False
        self._popped = False
        self._advance(initial=True)

    # ------------------------------------------------------------ motore
    def _apply_side_effects(self):
        """Consuma gli step non visivi in testa alla coda."""
        st = self.game.state
        while self.queue:
            step = self.queue[0]
            kind = step[0]
            if kind == "say":
                return "say"
            if kind == "choice":
                return "choice"
            self.queue.pop(0)
            if kind == "flag":
                st.set_flag(step[1], step[2])
            elif kind == "affinity":
                st.affinity[step[1]] = st.affinity.get(step[1], 0) + step[2]
            elif kind == "join":
                st.add_member(step[1])
                audio.sfx("levelup")
            elif kind == "give":
                st.add_item(step[1], step[2])
                audio.sfx("item")
            elif kind == "sfx":
                audio.sfx(step[1])
        return None

    def _advance(self, initial=False):
        kind = self._apply_side_effects()
        if kind is None:
            self.done = True
            # nel costruttore la scena non è ancora nello stack: il pop
            # effettivo avviene al primo update()
            if not initial and not self._popped:
                self._popped = True
                self.game.scenes.pop(None)
            return
        if kind == "say":
            _, who, txt = self.queue.pop(0)
            self.speaker = who
            self.text = txt
            self.lines = T.wrap(txt, 24, BOX_W - PORTRAIT - 90)
            self.shown = 0.0
            self.choice_menu = None
        elif kind == "choice":
            _, options = self.queue[0]
            self.choice_menu = ui.Menu([(label, i) for i, (label, _) in
                                        enumerate(options)], size=24)

    # ------------------------------------------------------------- input
    def handle_event(self, event):
        if self.done or event.type != pygame.KEYDOWN:
            return
        if self.choice_menu is not None:
            res = self.choice_menu.handle_event(event)
            if res == "confirm":
                _, options = self.queue.pop(0)
                _, steps = options[self.choice_menu.value]
                self.queue = list(steps) + self.queue
                self.choice_menu = None
                self._advance()
            return
        if event.key in KEYS_CONFIRM:
            if self.shown < len(self.text):
                self.shown = len(self.text)      # completa subito
            else:
                audio.sfx("confirm")
                self._advance()

    def update(self, dt):
        if self.done and not self._popped:
            self._popped = True
            self.game.scenes.pop(None)
            return
        if self.shown < len(self.text):
            self.shown = min(len(self.text), self.shown + CPS * dt)

    # ------------------------------------------------------------ disegno
    def draw(self, surface):
        if self.done:
            return
        info = CAST.get(self.speaker, CAST[""])
        # ritratto sopra il box, a sinistra
        if info["portrait"]:
            por = assets.portrait(info["portrait"], PORTRAIT)
            py = BOX_Y - PORTRAIT + 60
            surface.blit(por, (BOX_X + 8, py))
        surface.blit(ui.panel(BOX_W, BOX_H), (BOX_X, BOX_Y))
        tx = BOX_X + (PORTRAIT + 40 if info["portrait"] else 36)
        # targhetta col nome
        if info["name"]:
            name_w = assets.font("bold", 24).size(info["name"])[0] + 36
            tag = ui.panel(name_w, 40)
            surface.blit(tag, (tx - 14, BOX_Y - 22))
            T.draw(surface, info["name"], (tx + 2, BOX_Y - 16), 24,
                   C_ACCENT2, kind="bold")
        # testo con typewriter
        remaining = int(self.shown)
        y = BOX_Y + 34
        for line in self.lines:
            if remaining <= 0:
                break
            part = line[:remaining]
            remaining -= len(line)
            T.draw(surface, part, (tx, y), 24)
            y += 34
        # indicatore di avanzamento (triangolo: il font non ha il glifo ▼)
        if self.shown >= len(self.text) and self.choice_menu is None:
            ax, ay = BOX_X + BOX_W - 40, BOX_Y + BOX_H - 30
            pygame.draw.polygon(surface, C_ACCENT,
                                [(ax - 8, ay - 8), (ax + 8, ay - 8), (ax, ay + 2)])
        # scelte
        if self.choice_menu is not None and self.shown >= len(self.text):
            n = len(self.choice_menu.items)
            ch_w, ch_h = 640, n * 44 + 28
            cx = WIDTH - ch_w - 70
            cy = BOX_Y - ch_h - 12
            surface.blit(ui.panel(ch_w, ch_h), (cx, cy))
            self.choice_menu.draw(surface, cx + 46, cy + 18, 44)
