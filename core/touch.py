"""Controlli touch a schermo per la versione web su telefono/tablet.

L'overlay appare solo su dispositivi con schermo touch (web) e traduce i
tocchi negli stessi input che il gioco già capisce, senza toccare le scene:

- Croce direzionale (in basso a sinistra): mentre è premuta imposta
  `game.auto_dir` (il movimento in esplorazione) e invia i tasti freccia
  sintetici per navigare menu e battaglie (con auto-ripetizione).
- Tasto A (in basso a destra): SPAZIO — conferma / interagisci / avanza.
- Tasto B (sopra ad A): ESC — menu di pausa / annulla.

Su desktop e nei test l'overlay è disattivato e non fa nulla.
"""
import sys

import pygame

from settings import HEIGHT, WIDTH

IS_WEB = sys.platform == "emscripten"
REPEAT_DELAY = 0.32          # auto-ripetizione frecce nei menu (secondi)
DIR_KEYS = {(0, -1): pygame.K_UP, (0, 1): pygame.K_DOWN,
            (-1, 0): pygame.K_LEFT, (1, 0): pygame.K_RIGHT}


class TouchOverlay:
    def __init__(self, game):
        self.game = game
        self.enabled = False
        if IS_WEB:
            try:
                import platform
                self.enabled = int(platform.window.navigator.maxTouchPoints) > 0
            except Exception:
                self.enabled = False
        # geometria (coordinate schermo 1280x720)
        self.dpad_c = (170, HEIGHT - 170)
        self.dpad_r = 130
        self.a_c, self.a_r = (WIDTH - 120, HEIGHT - 130), 62
        self.b_c, self.b_r = (WIDTH - 265, HEIGHT - 215), 46
        self.fingers = {}        # finger_id -> zona ("dpad" | "a" | "b")
        self.dir = None
        self.repeat_t = 0.0
        self.pressed = {"a": False, "b": False}

    # ------------------------------------------------------------ geometria
    @staticmethod
    def _inside(pos, center, radius):
        dx, dy = pos[0] - center[0], pos[1] - center[1]
        return dx * dx + dy * dy <= radius * radius

    def _zone(self, x, y):
        if self._inside((x, y), self.a_c, self.a_r + 14):
            return "a"
        if self._inside((x, y), self.b_c, self.b_r + 14):
            return "b"
        if self._inside((x, y), self.dpad_c, self.dpad_r + 30):
            return "dpad"
        return None

    def _dpad_dir(self, x, y):
        dx, dy = x - self.dpad_c[0], y - self.dpad_c[1]
        if dx * dx + dy * dy < 26 * 26:      # zona morta al centro
            return None
        if abs(dx) > abs(dy):
            return (1, 0) if dx > 0 else (-1, 0)
        return (0, 1) if dy > 0 else (0, -1)

    # ---------------------------------------------------------------- input
    def _post_key(self, key):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))

    def _set_dir(self, d):
        if d != self.dir:
            self.dir = d
            self.game.auto_dir = d           # movimento in esplorazione
            if d is not None:
                self._post_key(DIR_KEYS[d])  # navigazione menu
                self.repeat_t = 0.0

    def handle_event(self, event):
        """True se l'evento è stato consumato dall'overlay."""
        if not self.enabled:
            return False
        if event.type == pygame.FINGERDOWN:
            x, y = event.x * WIDTH, event.y * HEIGHT
            zone = self._zone(x, y)
            if zone is None:
                return False
            self.fingers[event.finger_id] = zone
            if zone == "dpad":
                self._set_dir(self._dpad_dir(x, y))
            elif zone == "a":
                self.pressed["a"] = True
                self._post_key(pygame.K_SPACE)
            elif zone == "b":
                self.pressed["b"] = True
                self._post_key(pygame.K_ESCAPE)
            return True
        if event.type == pygame.FINGERMOTION:
            if self.fingers.get(event.finger_id) == "dpad":
                x, y = event.x * WIDTH, event.y * HEIGHT
                self._set_dir(self._dpad_dir(x, y))
                return True
            return False
        if event.type == pygame.FINGERUP:
            zone = self.fingers.pop(event.finger_id, None)
            if zone == "dpad" and "dpad" not in self.fingers.values():
                self._set_dir(None)
            elif zone in ("a", "b"):
                self.pressed[zone] = False
            return zone is not None
        return False

    def update(self, dt):
        if not self.enabled or self.dir is None:
            return
        self.repeat_t += dt                  # auto-ripetizione nei menu
        if self.repeat_t >= REPEAT_DELAY:
            self.repeat_t = 0.0
            self._post_key(DIR_KEYS[self.dir])

    # ---------------------------------------------------------------- draw
    def draw(self, surface):
        if not self.enabled:
            return
        from core import text as T
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        cx, cy = self.dpad_c
        pygame.draw.circle(ov, (16, 22, 34, 110), (cx, cy), self.dpad_r)
        pygame.draw.circle(ov, (86, 214, 220, 90), (cx, cy), self.dpad_r, 3)
        for d in DIR_KEYS:
            px, py = cx + d[0] * 78, cy + d[1] * 78
            active = self.dir == d
            col = (86, 214, 220, 235) if active else (235, 240, 248, 130)
            pts = []
            for base in ((-22, 14), (22, 14), (0, -20)):
                bx, by = base
                if d == (0, 1):
                    bx, by = bx, -by
                elif d == (-1, 0):
                    bx, by = by - 3, bx
                elif d == (1, 0):
                    bx, by = -by + 3, bx
                pts.append((px + bx, py + by))
            pygame.draw.polygon(ov, col, pts)
        for center, radius, label, key in (
                (self.a_c, self.a_r, "A", "a"), (self.b_c, self.b_r, "B", "b")):
            fill = (86, 214, 220, 200) if self.pressed[key] else (16, 22, 34, 130)
            pygame.draw.circle(ov, fill, center, radius)
            pygame.draw.circle(ov, (255, 176, 92, 160), center, radius, 3)
        surface.blit(ov, (0, 0))
        T.draw(surface, "A", (self.a_c[0], self.a_c[1] - 18), 34,
               (255, 176, 92), kind="bold", align="center")
        T.draw(surface, "B", (self.b_c[0], self.b_c[1] - 15), 28,
               (255, 176, 92), kind="bold", align="center")
