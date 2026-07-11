"""Widget UI: pannelli 9-slice, barre, menu a lista, numeri fluttuanti."""
import pygame

from asset_loader import assets
from core import text as T
from core.audio import audio
from settings import (C_ACCENT, C_PANEL, C_PANEL_EDGE, C_TEXT, C_TEXT_DIM,
                      KEYS_CANCEL, KEYS_CONFIRM, KEYS_DOWN, KEYS_UP)

_panel_cache = {}
_veil_cache = {}


def veil(color_rgba, size=None):
    """Velo a schermo intero (o `size`) con cache: evita una Surface per frame."""
    from settings import HEIGHT, WIDTH
    size = size or (WIDTH, HEIGHT)
    key = (color_rgba, size)
    if key not in _veil_cache:
        if len(_veil_cache) > 16:
            _veil_cache.clear()
        s = pygame.Surface(size, pygame.SRCALPHA)
        s.fill(color_rgba)
        _veil_cache[key] = s
    return _veil_cache[key]


def panel(w, h, alpha=235):
    """Pannello 9-slice da ui/panel.png (fallback: rettangolo scuro bordato)."""
    key = (w, h, alpha)
    if key in _panel_cache:
        return _panel_cache[key]
    if len(_panel_cache) > 60:
        _panel_cache.clear()
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if assets.has_ui("panel"):
        # base scura sotto il pannello "vetro": migliora la leggibilità
        pygame.draw.rect(surf, C_PANEL + (205,),
                         pygame.Rect(2, 2, w - 4, h - 4), border_radius=12)
        src = assets.ui("panel")
        b = max(8, min(16, src.get_width() // 3 - 1, src.get_height() // 3 - 1))
        sw, sh = src.get_size()
        cols = [(0, b), (b, sw - 2 * b), (sw - b, b)]
        rows = [(0, b), (b, sh - 2 * b), (sh - b, b)]
        dcols = [(0, b), (b, w - 2 * b), (w - b, b)]
        drows = [(0, b), (b, h - 2 * b), (h - b, b)]
        for r in range(3):
            for c in range(3):
                sx, sws = cols[c]
                sy, shs = rows[r]
                dx, dws = dcols[c]
                dy, dhs = drows[r]
                if sws <= 0 or shs <= 0 or dws <= 0 or dhs <= 0:
                    continue
                piece = src.subsurface(pygame.Rect(sx, sy, sws, shs))
                surf.blit(pygame.transform.scale(piece, (dws, dhs)), (dx, dy))
        if alpha < 255:
            surf.set_alpha(alpha)
    else:
        pygame.draw.rect(surf, C_PANEL + (alpha,), surf.get_rect(), border_radius=10)
        pygame.draw.rect(surf, C_PANEL_EDGE + (255,), surf.get_rect(), 2, border_radius=10)
    _panel_cache[key] = surf
    return surf


def draw_bar(surface, x, y, w, h, ratio, color, back=(30, 36, 50)):
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, back, (x, y, w, h), border_radius=h // 2)
    if ratio > 0:
        pygame.draw.rect(surface, color, (x, y, max(h, int(w * ratio)), h),
                         border_radius=h // 2)
    pygame.draw.rect(surface, (70, 82, 104), (x, y, w, h), 1, border_radius=h // 2)


class Menu:
    """Lista verticale navigabile. items: [(label, value)] o [label]."""

    def __init__(self, items, size=24, enabled=None):
        self.set_items(items, enabled)
        self.size = size
        self.index = 0

    def set_items(self, items, enabled=None):
        self.items = [(i, i) if isinstance(i, str) else i for i in items]
        self.enabled = enabled if enabled is not None else [True] * len(self.items)

    @property
    def value(self):
        return self.items[self.index][1] if self.items else None

    def handle_event(self, event):
        """Ritorna 'confirm' | 'cancel' | None."""
        if event.type != pygame.KEYDOWN or not self.items:
            return None
        if event.key in KEYS_UP:
            self.index = (self.index - 1) % len(self.items)
            audio.sfx("move")
        elif event.key in KEYS_DOWN:
            self.index = (self.index + 1) % len(self.items)
            audio.sfx("move")
        elif event.key in KEYS_CONFIRM:
            if self.enabled[self.index]:
                audio.sfx("confirm")
                return "confirm"
            audio.sfx("cancel")
        elif event.key in KEYS_CANCEL:
            audio.sfx("cancel")
            return "cancel"
        return None

    def draw(self, surface, x, y, spacing=None, align="left", width=None):
        spacing = spacing or (self.size + 14)
        for i, (label, _) in enumerate(self.items):
            sel = i == self.index
            col = C_TEXT if self.enabled[i] else C_TEXT_DIM
            if sel:
                if width:
                    hl = pygame.Surface((width, spacing - 4), pygame.SRCALPHA)
                    hl.fill(C_ACCENT + (36,))
                    surface.blit(hl, (x - 26, y + i * spacing - 4))
                cy = y + i * spacing + self.size // 2 + 2
                pygame.draw.polygon(surface, C_ACCENT,
                                    [(x - 22, cy - 7), (x - 22, cy + 7),
                                     (x - 10, cy)])
                col = C_ACCENT if self.enabled[i] else C_TEXT_DIM
            T.draw(surface, label, (x, y + i * spacing), self.size, col, align=align)
        return y + len(self.items) * spacing


class FloatingText:
    def __init__(self, txt, pos, color, size=26):
        self.txt, self.color, self.size = txt, color, size
        self.x, self.y = pos
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        self.y -= 46 * dt
        return self.t < 1.0

    def draw(self, surface):
        T.draw(surface, self.txt, (self.x, self.y), self.size, self.color,
               kind="bold", align="center")
