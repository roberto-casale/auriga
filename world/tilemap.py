"""Mappa a tile: parsing ASCII, collisioni, disegno con telecamera."""
import math

import pygame

from asset_loader import assets
from settings import HEIGHT, TILE, WIDTH
from world.mapdata import LEGEND, MAPS


class Camera:
    def __init__(self, map_w, map_h):
        self.x = 0.0
        self.y = 0.0
        self.map_w, self.map_h = map_w, map_h

    def follow(self, px, py):
        self.x = px - WIDTH / 2
        self.y = py - HEIGHT / 2
        # coordinate intere: mappa pre-renderizzata ed entità restano allineate
        self.x = int(max(0, min(self.x, self.map_w - WIDTH)))
        self.y = int(max(0, min(self.y, self.map_h - HEIGHT)))

    def apply(self, x, y):
        return int(x - self.x), int(y - self.y)


_GLOW_FRAMES = []


def _glow_frame(pulse01):
    """Glow del savepoint pre-renderizzato (16 fasi), niente Surface per frame."""
    if not _GLOW_FRAMES:
        for i in range(16):
            p = i / 15
            g = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            pygame.draw.circle(g, (86, 214, 220, int(40 + 60 * p)),
                               (TILE // 2, TILE // 2), TILE // 2 - 4)
            _GLOW_FRAMES.append(g)
    return _GLOW_FRAMES[max(0, min(15, int(pulse01 * 15)))]


class TileMap:
    """Interpreta i dati di world.mapdata per una singola mappa."""

    def __init__(self, map_id, state):
        self.id = map_id
        self.data = MAPS[map_id]
        self.state = state
        self.rows = self.data["rows"]
        self.h = len(self.rows)
        self.w = max(len(r) for r in self.rows)
        self.rows = [r.ljust(self.w, "#") for r in self.rows]
        self.legend = dict(LEGEND)
        self.legend.update(self.data.get("legend", {}))
        self.floor_name = self.data.get("floor", "floor_ship_a")
        self.time = 0.0
        # trigger indicizzati per posizione
        self.triggers = {}
        for tr in self.data.get("triggers", []):
            self.triggers[(tr["x"], tr["y"])] = tr
        # celle il cui aspetto cambia a runtime (bauli, anomalie, porte, save)
        self._dyn = set()
        for (x, y), tr in self.triggers.items():
            if "chest" in tr or "battle" in tr or "transfer" in tr:
                self._dyn.add((x, y))
        for y in range(self.h):
            for x in range(self.w):
                if self.char_at(x, y) == "S":
                    self._dyn.add((x, y))
        self._static = None      # mappa pre-renderizzata (celle non dinamiche)

    # ------------------------------------------------------------- query
    def char_at(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.rows[y][x]
        return "#"

    def spec(self, x, y):
        return self.legend.get(self.char_at(x, y), LEGEND["#"])

    def is_solid(self, x, y, entities=()):
        if self.spec(x, y).get("solid", False):
            return True
        for e in entities:
            if e.x == x and e.y == y:
                return True
        return False

    def trigger_at(self, x, y):
        tr = self.triggers.get((x, y))
        if tr is None:
            return None
        if tr.get("once") and tr["id"] in self.state.done:
            return None
        req = tr.get("requires_flag")
        if req and not self.state.flag(req):
            if tr.get("on") == "enter" and "transfer" not in tr:
                return None            # gli enter condizionati spariscono
        return tr

    @property
    def pixel_size(self):
        return self.w * TILE, self.h * TILE

    # ------------------------------------------------------------ disegno
    def _tile_for(self, ch, x, y):
        """Nome del tile oggetto da disegnare sopra il pavimento (o None)."""
        spec = self.legend.get(ch)
        if spec is None or spec.get("tile") is None:
            return None
        name = spec["tile"]
        tr = self.triggers.get((x, y))
        if tr is not None:
            if "chest" in tr:
                name = "chest_open" if tr["id"] in self.state.done else "chest_closed"
            elif "battle" in tr and tr["id"] in self.state.done:
                return None            # anomalia ripulita
            elif "transfer" in tr and ch == "D":
                req = tr.get("requires_flag")
                name = "door_closed" if (req and not self.state.flag(req)) else "door_open"
        return name

    def _build_static(self):
        """Pre-renderizza l'intera mappa (tranne le celle dinamiche): il draw
        per frame diventa un singolo blit invece di ~480."""
        surf = pygame.Surface((self.w * TILE, self.h * TILE))
        surf.fill((6, 8, 14))
        floor_img = assets.tile(self.floor_name)
        for y in range(self.h):
            for x in range(self.w):
                ch = self.char_at(x, y)
                spec = self.legend.get(ch, LEGEND["#"])
                base = spec.get("floor", self.floor_name)
                if not spec.get("no_floor"):
                    surf.blit(floor_img if base == self.floor_name
                              else assets.tile(base), (x * TILE, y * TILE))
                if (x, y) in self._dyn:
                    continue                     # l'oggetto si disegna al volo
                name = self._tile_for(ch, x, y)
                if name:
                    surf.blit(assets.tile(name), (x * TILE, y * TILE))
        if pygame.display.get_surface() is not None:
            surf = surf.convert()
        return surf

    def draw(self, surface, cam):
        self.time += 1 / 60
        if self._static is None:
            self._static = self._build_static()
        surface.blit(self._static, (0, 0),
                     pygame.Rect(int(cam.x), int(cam.y), WIDTH, HEIGHT))
        # solo le poche celle dinamiche vengono ridisegnate ogni frame
        for (x, y) in self._dyn:
            sx, sy = cam.apply(x * TILE, y * TILE)
            if sx < -TILE or sy < -TILE or sx > WIDTH or sy > HEIGHT:
                continue
            ch = self.char_at(x, y)
            name = self._tile_for(ch, x, y)
            if name:
                surface.blit(assets.tile(name), (sx, sy))
            if ch == "S":              # pulsazione del punto di salvataggio
                pulse = (math.sin(self.time * 3) + 1) / 2
                surface.blit(_glow_frame(pulse), (sx, sy))
