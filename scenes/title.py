"""Schermata del titolo."""
import math

import pygame

from asset_loader import assets
from core import text as T
from core import ui
from core.audio import audio
from core.scene import Scene
from game.party import new_game_state
from scenes.menu import SaveMenuScene
from settings import (C_ACCENT, C_ACCENT2, C_TEXT, C_TEXT_DIM, GAME_TITLE,
                      HEIGHT, VERSION, WIDTH)


class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.menu = ui.Menu([("Nuova partita", "new"), ("Carica partita", "load"),
                             ("Esci", "quit")], size=30)
        self.t = 0.0
        audio.play_music("title")

    def handle_event(self, event):
        res = self.menu.handle_event(event)
        if res != "confirm":
            return
        v = self.menu.value
        if v == "new":
            self.game.state = new_game_state()
            from scenes.explore import ExploreScene
            audio.stop_music()
            self.game.scenes.clear_to(ExploreScene(self.game))
        elif v == "load":
            self.game.scenes.push(SaveMenuScene(self.game, "load"))
        elif v == "quit":
            self.game.running = False

    def update(self, dt):
        self.t += dt

    def draw(self, surface):
        surface.blit(assets.background("title"), (0, 0))
        surface.blit(ui.veil((8, 10, 20, 70)), (0, 0))
        glow = 0.5 + 0.5 * math.sin(self.t * 1.4)
        T.draw(surface, "AURIGA", (WIDTH // 2, 130), 110,
               C_ACCENT2, kind="title", align="center")
        T.draw(surface, "— Il Richiamo dei Tessitori —", (WIDTH // 2, 265), 32,
               (int(150 + 80 * glow), int(214 + 20 * glow), 220),
               kind="text", align="center")
        w, h = 380, 210
        x, y = (WIDTH - w) // 2, 400
        surface.blit(ui.panel(w, h), (x, y))
        self.menu.draw(surface, x + 110, y + 36, 52)
        T.draw(surface, f"v{VERSION} — pygame — un racconto sci-fi a turni",
               (WIDTH // 2, HEIGHT - 40), 18, C_TEXT_DIM, align="center")
