"""Rendering testo: cache, ombra, a capo automatico."""
import pygame

from asset_loader import assets
from settings import C_SHADOW, C_TEXT

_cache = {}


def render(text, size=22, color=C_TEXT, kind="text"):
    key = (text, size, color, kind)
    if key not in _cache:
        if len(_cache) > 900:            # cache bounded
            _cache.clear()
        _cache[key] = assets.font(kind, size).render(text, True, color)
    return _cache[key]


def draw(surface, text, pos, size=22, color=C_TEXT, kind="text",
         align="left", shadow=True):
    img = render(text, size, color, kind)
    x, y = pos
    if align == "center":
        x -= img.get_width() // 2
    elif align == "right":
        x -= img.get_width()
    if shadow:
        surface.blit(render(text, size, C_SHADOW, kind), (x + 2, y + 2))
    surface.blit(img, (x, y))
    return img.get_rect(topleft=(x, y))


def wrap(text, size, max_width, kind="text"):
    """Divide il testo in righe che stanno in max_width pixel."""
    font = assets.font(kind, size)
    lines = []
    for raw_line in text.split("\n"):
        words = raw_line.split(" ")
        line = ""
        for w in words:
            trial = (line + " " + w).strip()
            if font.size(trial)[0] <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = w
        lines.append(line)
    return lines
