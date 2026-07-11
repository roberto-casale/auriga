"""Caricamento centralizzato degli asset da ./assets/.

Tutta la grafica/audio del gioco passa da qui (vedi ASSET_CONTRACT.md).
Se un file manca viene generato un segnaposto colorato: il gioco non deve
mai crashare per un asset assente.
"""
import json
import os

import pygame

from settings import ASSETS_DIR, TILE, WIDTH, HEIGHT

_WALK_ORDER = ["down", "left", "right", "up"]


def _hash_color(name):
    h = 0
    for ch in name:
        h = (h * 131 + ord(ch)) % 0xFFFFFF
    r, g, b = 60 + (h & 0x7F), 60 + ((h >> 8) & 0x7F), 60 + ((h >> 16) & 0x7F)
    return (r, g, b)


def _convert(surf, alpha=True):
    """convert/convert_alpha solo se esiste una display surface.

    I blit di superfici opache (sfondi a schermo intero) sono ~3x più veloci
    con convert() rispetto a convert_alpha().
    """
    if pygame.display.get_surface() is not None:
        return surf.convert_alpha() if alpha else surf.convert()
    return surf


class Assets:
    """Registro (lazy) di immagini, suoni e font. Istanza unica in `assets`."""

    def __init__(self):
        self._tiles = {}
        self._sheets = {}
        self._portraits = {}
        self._ui = {}
        self._bgs = {}
        self._sfx = {}
        self._fonts = {}
        self._char_meta = None
        self.missing = []          # path richiesti ma non trovati (per diagnostica)
        self.sfx_enabled = True

    # ------------------------------------------------------------- util
    def _path(self, *parts):
        return os.path.join(ASSETS_DIR, *parts)

    def _load_image(self, relpath):
        p = self._path(*relpath.split("/"))
        if os.path.isfile(p):
            try:
                return _convert(pygame.image.load(p))
            except pygame.error:
                self.missing.append(relpath + " (corrotto)")
                return None
        self.missing.append(relpath)
        return None

    def _placeholder(self, name, size, alpha=False):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        col = _hash_color(name)
        if alpha:
            pygame.draw.rect(surf, col + (230,), surf.get_rect(), border_radius=6)
        else:
            surf.fill(col)
        pygame.draw.rect(surf, (250, 250, 250), surf.get_rect(), 2)
        try:
            f = pygame.font.Font(None, max(14, size[1] // 3))
            letter = f.render(name[:2].upper(), True, (255, 255, 255))
            surf.blit(letter, letter.get_rect(center=surf.get_rect().center))
        except pygame.error:
            pass
        return surf

    # ------------------------------------------------------------- tiles
    def tile(self, name):
        if name not in self._tiles:
            img = self._load_image(f"tiles/{name}.png")
            if img is None:
                img = self._placeholder(name, (TILE, TILE))
            elif img.get_size() != (TILE, TILE):
                img = pygame.transform.scale(img, (TILE, TILE))
            self._tiles[name] = img
        return self._tiles[name]

    # ------------------------------------------------------- spritesheet
    def _meta(self):
        if self._char_meta is None:
            p = self._path("characters", "meta.json")
            self._char_meta = {"layout": "3x4", "order": _WALK_ORDER, "sheets": {}}
            if os.path.isfile(p):
                try:
                    with open(p, encoding="utf-8") as fh:
                        self._char_meta.update(json.load(fh))
                except (json.JSONDecodeError, OSError):
                    pass
        return self._char_meta

    def char_frames(self, name):
        """dict direzione -> [3 frame] scalati (altezza ~ TILE*1.12)."""
        if name in self._sheets:
            return self._sheets[name]
        img = self._load_image(f"characters/{name}.png")
        frames = {}
        if img is not None:
            info = self._meta()["sheets"].get(name, {})
            fw = int(info.get("fw", img.get_width() // 3))
            fh = int(info.get("fh", img.get_height() // 4))
            fw = max(1, fw)
            fh = max(1, fh)
            order = self._meta().get("order", _WALK_ORDER)
            target_h = int(TILE * 1.12)
            scale = target_h / fh
            tw, th = max(1, int(fw * scale)), target_h
            for row, dname in enumerate(order):
                row_frames = []
                for col in range(3):
                    rect = pygame.Rect(col * fw, row * fh, fw, fh)
                    if rect.right <= img.get_width() and rect.bottom <= img.get_height():
                        fr = img.subsurface(rect)
                        row_frames.append(pygame.transform.scale(fr, (tw, th)))
                if row_frames:
                    frames[dname] = row_frames
        if not frames:
            ph = self._placeholder(name, (int(TILE * 0.8), int(TILE * 1.12)), alpha=True)
            frames = {d: [ph, ph, ph] for d in _WALK_ORDER}
        for d in _WALK_ORDER:            # garantisce tutte le direzioni
            frames.setdefault(d, frames[next(iter(frames))])
        self._sheets[name] = frames
        return frames

    def enemy_sprite(self, name, min_side=96):
        """Sprite statico nemico (assets/characters/enemy_*.png)."""
        key = ("enemy", name)
        if key not in self._sheets:
            img = self._load_image(f"characters/{name}.png")
            if img is None:
                img = self._placeholder(name, (min_side, min_side), alpha=True)
            elif max(img.get_size()) < min_side:
                sc = min_side / max(img.get_size())
                img = pygame.transform.scale(
                    img, (max(1, int(img.get_width() * sc)), max(1, int(img.get_height() * sc))))
            self._sheets[key] = img
        return self._sheets[key]

    # --------------------------------------------------------- portraits
    def portrait(self, name, size=300):
        key = (name, size)
        if key not in self._portraits:
            img = self._load_image(f"portraits/{name}.png")
            if img is None:
                img = self._placeholder("volto:" + name, (size, size), alpha=True)
            elif img.get_size() != (size, size):
                img = pygame.transform.smoothscale(img, (size, size))
            self._portraits[key] = img
        return self._portraits[key]

    # ---------------------------------------------------------------- ui
    def ui(self, name, size=None):
        key = (name, size)
        if key not in self._ui:
            img = self._load_image(f"ui/{name}.png")
            if img is None:
                img = self._placeholder(name, size or (48, 48), alpha=True)
            elif size is not None and img.get_size() != size:
                img = pygame.transform.smoothscale(img, size)
            self._ui[key] = img
        return self._ui[key]

    def has_ui(self, name):
        return os.path.isfile(self._path("ui", name + ".png"))

    # ------------------------------------------------------- backgrounds
    def background(self, name, size=(WIDTH, HEIGHT)):
        key = (name, size)
        if key not in self._bgs:
            img = self._load_image(f"backgrounds/{name}.png")
            if img is not None and pygame.display.get_surface() is not None:
                img = img.convert()          # opaco: blit molto più economico
            if img is None:
                surf = pygame.Surface(size)
                top, bottom = (10, 14, 30), (40, 20, 60)
                for y in range(size[1]):
                    t = y / max(1, size[1] - 1)
                    col = tuple(int(a + (b - a) * t) for a, b in zip(top, bottom))
                    pygame.draw.line(surf, col, (0, y), (size[0], y))
                img = surf
            elif img.get_size() != size:
                img = pygame.transform.smoothscale(img, size)
            self._bgs[key] = img
        return self._bgs[key]

    def space_tile(self):
        if ("space",) not in self._bgs:
            img = self._load_image("backgrounds/space.png")
            if img is None:
                img = pygame.Surface((256, 256))
                img.fill((8, 10, 22))
                for i in range(90):
                    x = (i * 97) % 256
                    y = (i * 57 + i * i) % 256
                    c = 120 + (i * 43) % 130
                    img.set_at((x, y), (c, c, min(255, c + 20)))
            self._bgs[("space",)] = img
        return self._bgs[("space",)]

    # -------------------------------------------------------------- font
    def font(self, kind, size):
        """kind: 'title' | 'text' | 'bold'."""
        key = (kind, size)
        if key not in self._fonts:
            fname = {"title": "title.ttf", "text": "text.ttf", "bold": "text_bold.ttf"}.get(kind, "text.ttf")
            p = self._path("fonts", fname)
            try:
                if os.path.isfile(p):
                    self._fonts[key] = pygame.font.Font(p, size)
                else:
                    self.missing.append("fonts/" + fname)
                    self._fonts[key] = pygame.font.Font(None, int(size * 1.15))
            except (pygame.error, OSError):
                self._fonts[key] = pygame.font.Font(None, int(size * 1.15))
        return self._fonts[key]

    # ------------------------------------------------------------- audio
    def sfx(self, name):
        if not self.sfx_enabled:
            return None
        if name not in self._sfx:
            snd = None
            for ext in (".ogg", ".wav"):
                p = self._path("sfx", name + ext)
                if os.path.isfile(p):
                    try:
                        snd = pygame.mixer.Sound(p)
                        break
                    except pygame.error:
                        pass
            if snd is None:
                self.missing.append(f"sfx/{name}")
            self._sfx[name] = snd
        return self._sfx[name]

    def music_path(self, name):
        for ext in (".ogg", ".wav"):
            p = self._path("music", name + ext)
            if os.path.isfile(p):
                return p
        self.missing.append(f"music/{name}")
        return None


assets = Assets()
