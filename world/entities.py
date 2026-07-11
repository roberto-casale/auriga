"""Entità sulla mappa: giocatore e NPC, con movimento a griglia interpolato."""
import pygame

from asset_loader import assets
from settings import DIRS, TILE

WALK_SPEED = 6.5           # tile al secondo
ANIM_FPS = 8


class Entity:
    def __init__(self, sheet, x, y, facing="down", name=""):
        self.sheet = sheet
        self.name = name
        self.x, self.y = x, y                  # cella di arrivo
        self.px, self.py = float(x), float(y)  # posizione fluida in tile
        self.facing = facing
        self.moving = False
        self.anim_t = 0.0

    def try_move(self, dx, dy, tilemap, entities=(), player=None):
        """Avvia il movimento verso la cella adiacente se libera."""
        if self.moving:
            return False
        self.facing = {(0, 1): "down", (0, -1): "up",
                       (-1, 0): "left", (1, 0): "right"}[(dx, dy)]
        nx, ny = self.x + dx, self.y + dy
        blockers = [e for e in entities if e is not self]
        if player is not None and player is not self:
            blockers.append(player)
        if tilemap.is_solid(nx, ny, blockers):
            return False
        self.x, self.y = nx, ny
        self.moving = True
        return True

    def update(self, dt):
        self.anim_t += dt
        if not self.moving:
            return
        tx, ty = float(self.x), float(self.y)
        step = WALK_SPEED * dt
        self.px += max(-step, min(step, tx - self.px))
        self.py += max(-step, min(step, ty - self.py))
        if abs(tx - self.px) < 1e-4 and abs(ty - self.py) < 1e-4:
            self.px, self.py = tx, ty
            self.moving = False

    def facing_cell(self):
        dx, dy = DIRS[self.facing]
        return self.x + dx, self.y + dy

    def frame(self):
        frames = assets.char_frames(self.sheet)[self.facing]
        if self.moving:
            seq = (0, 1, 2, 1)
            i = seq[int(self.anim_t * ANIM_FPS) % 4]
        else:
            i = 1 if len(frames) > 1 else 0
        return frames[min(i, len(frames) - 1)]

    def draw(self, surface, cam):
        img = self.frame()
        sx, sy = cam.apply(self.px * TILE, self.py * TILE)
        # ancorato in basso al centro della cella
        surface.blit(img, (sx + (TILE - img.get_width()) // 2,
                           sy + TILE - img.get_height()))

    @property
    def draw_order(self):
        return self.py


class NPC(Entity):
    def __init__(self, spec):
        super().__init__(spec["sheet"], spec["x"], spec["y"],
                         spec.get("facing", "down"), spec.get("name", ""))
        self.event = spec.get("event")
        self.visible_flag = spec.get("visible_flag")     # mostra solo se flag
        self.hidden_flag = spec.get("hidden_flag")       # nascondi se flag

    def active(self, state):
        if self.visible_flag and not state.flag(self.visible_flag):
            return False
        if self.hidden_flag and state.flag(self.hidden_flag):
            return False
        return True

    def face_towards(self, x, y):
        dx, dy = x - self.x, y - self.y
        if abs(dx) > abs(dy):
            self.facing = "right" if dx > 0 else "left"
        elif dy != 0:
            self.facing = "down" if dy > 0 else "up"
