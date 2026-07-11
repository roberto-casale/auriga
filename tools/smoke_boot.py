"""Smoke test: avvio headless, nuova partita, qualche frame, screenshot.

Uso (da auriga/):  ../.venv/bin/python tools/smoke_boot.py [cartella_screenshot]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from main import Game  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else None
DT = 1 / 60


def shot(game, name):
    if OUT:
        os.makedirs(OUT, exist_ok=True)
        pygame.image.save(game.screen, os.path.join(OUT, name + ".png"))


def frames(game, n):
    for _ in range(n):
        game.step(DT, [])


def press(game, key):
    game.step(DT, [pygame.event.Event(pygame.KEYDOWN, key=key)])
    frames(game, 3)


def main():
    game = Game()
    frames(game, 10)
    shot(game, "01_title")
    press(game, pygame.K_SPACE)          # Nuova partita
    frames(game, 30)
    shot(game, "02_intro")
    for _ in range(30):                  # dialogo introduttivo
        press(game, pygame.K_SPACE)
    frames(game, 30)
    shot(game, "03_explore")
    press(game, pygame.K_ESCAPE)         # menu di pausa
    frames(game, 5)
    shot(game, "04_pause")
    press(game, pygame.K_ESCAPE)
    frames(game, 5)
    from scenes.explore import ExploreScene
    assert isinstance(game.scenes.current, ExploreScene), \
        f"scena inattesa: {type(game.scenes.current).__name__}"
    assert game.state.map_id == "habitat"
    print("SMOKE BOOT OK — titolo, nuova partita, intro, esplorazione, pausa")


if __name__ == "__main__":
    main()
