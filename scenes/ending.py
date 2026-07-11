"""Scena finale: epilogo a scorrimento e ritorno al titolo."""
import pygame

from asset_loader import assets
from core import text as T
from core import ui
from core.audio import audio
from core.scene import Scene
from game.story import ending_lines
from settings import (C_ACCENT2, C_TEXT, C_TEXT_DIM, HEIGHT, KEYS_CONFIRM,
                      WIDTH)

SCROLL_SPEED = 34            # pixel al secondo
LINE_H = 40


class EndingScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.lines = ending_lines(game.state)
        self.offset = 0.0
        self.total_h = len(self.lines) * LINE_H
        audio.play_music("ending")

    @property
    def finished(self):
        return self.offset >= self.total_h + HEIGHT // 3

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in KEYS_CONFIRM:
            if self.finished:
                from scenes.title import TitleScene
                audio.stop_music()
                self.game.scenes.clear_to(TitleScene(self.game))
            else:
                self.offset += 120        # accelera la lettura

    def update(self, dt):
        if not self.finished:
            self.offset += SCROLL_SPEED * dt

    def draw(self, surface):
        surface.blit(assets.background("ending"), (0, 0))
        surface.blit(ui.veil((8, 8, 18, 130)), (0, 0))
        y0 = HEIGHT - int(self.offset)
        for i, line in enumerate(self.lines):
            y = y0 + i * LINE_H
            if -LINE_H < y < HEIGHT + LINE_H:
                big = line.startswith("~") or line.startswith("AURIGA")
                T.draw(surface, line, (WIDTH // 2, y),
                       34 if big else 24,
                       C_ACCENT2 if big else C_TEXT,
                       kind="title" if big else "text", align="center")
        if self.finished:
            T.draw(surface, "SPAZIO per tornare al titolo",
                   (WIDTH // 2, HEIGHT - 60), 20, C_TEXT_DIM, align="center")
