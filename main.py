"""AURIGA — Il Richiamo dei Tessitori.

Avvio nativo (dalla cartella auriga/):  ../.venv/bin/python main.py
Build web (browser):                    ../.venv/bin/pygbag main.py

Il ciclo di gioco è `async` con `await asyncio.sleep(0)` a ogni frame: è ciò che
pygbag richiede per girare in WebAssembly, e da nativo si comporta in modo
identico. `step()` resta sincrono, così gli strumenti in tools/ lo pilotano.
"""
import asyncio
import os
import sys

import pygame

# permette l'avvio anche da fuori dalla cartella auriga/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# True quando gira nel browser (pygbag/emscripten): alcune funzioni di I/O
# su file vanno gestite diversamente.
IS_WEB = sys.platform == "emscripten"

from core.audio import audio                      # noqa: E402
from core.scene import SceneManager               # noqa: E402
from core.touch import TouchOverlay               # noqa: E402
from settings import FPS, GAME_TITLE, HEIGHT, WIDTH  # noqa: E402


class Game:
    def __init__(self):
        pygame.init()
        audio.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.scenes = SceneManager()
        self.state = None
        self.running = True
        self.auto_dir = None      # direzione forzata dai test automatici
        self.touch = TouchOverlay(self)   # tasti a schermo (solo web touch)
        from scenes.title import TitleScene
        self.scenes.push(TitleScene(self))

    def step(self, dt, events):
        """Un frame di gioco: eventi, update, disegno (usato anche dai test)."""
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                return
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_F12
                    and not IS_WEB):
                pygame.image.save(self.screen, "screenshot.png")
                continue
            if self.touch.handle_event(event):
                continue
            scene = self.scenes.current
            if scene is not None:
                scene.handle_event(event)
        scene = self.scenes.current
        if scene is None:
            self.running = False
            return
        scene.update(dt)
        self.touch.update(dt)
        self.scenes.draw(self.screen)
        self.touch.draw(self.screen)
        pygame.display.flip()

    async def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            self.step(dt, pygame.event.get())
            await asyncio.sleep(0)          # cede il controllo al browser
        pygame.quit()


async def main():
    await Game().run()


if __name__ == "__main__":
    asyncio.run(main())
