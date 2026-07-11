"""Costanti globali di AURIGA."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SAVES_DIR = os.path.join(BASE_DIR, "saves")

GAME_TITLE = "AURIGA — Il Richiamo dei Tessitori"
VERSION = "1.0"

WIDTH, HEIGHT = 1280, 720
FPS = 60
TILE = 48                      # dimensione tile a schermo (sorgenti 16px upscalate 3x)

# --- palette UI ---
C_TEXT = (235, 240, 248)
C_TEXT_DIM = (150, 160, 178)
C_ACCENT = (86, 214, 220)      # ciano Tessitori
C_ACCENT2 = (255, 176, 92)     # ambra Auriga
C_WARN = (255, 106, 106)
C_GOOD = (126, 226, 148)
C_PANEL = (16, 22, 34)
C_PANEL_EDGE = (74, 96, 128)
C_SHADOW = (8, 10, 16)
C_HP = (110, 220, 150)
C_EN = (100, 180, 250)
C_XP = (240, 200, 110)

# --- elementi (stile HSR) ---
ELEMENTS = {
    "cinetico": {"name": "Cinetico", "color": (216, 176, 130), "icon": "icon_kinetic"},
    "termico":  {"name": "Termico",  "color": (255, 128, 96),  "icon": "icon_thermal"},
    "ionico":   {"name": "Ionico",   "color": (120, 190, 255), "icon": "icon_ion"},
    "bio":      {"name": "Bio",      "color": (140, 230, 130), "icon": "icon_bio"},
}
WEAK_MULT = 1.5
RESIST_MULT = 0.5

# --- gameplay (difficoltà: facile) ---
CRIT_CHANCE = 0.12
CRIT_MULT = 1.5
FLEE_CHANCE = 0.92
EN_REGEN_PER_TURN = 4          # energia recuperata da ogni personaggio a inizio turno
LEVELUP_HEAL_FRAC = 0.35       # cura gratuita al level up
DEFEAT_HP_FRAC = 0.5           # HP al respawn dopo una sconfitta

MAX_PARTY = 4
MAX_ITEM_STACK = 9
SAVE_SLOTS = 3

# --- input ---
import pygame  # noqa: E402  (solo per le costanti dei tasti)

KEYS_CONFIRM = (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z)
KEYS_CANCEL = (pygame.K_ESCAPE, pygame.K_x, pygame.K_BACKSPACE)
KEYS_UP = (pygame.K_UP, pygame.K_w)
KEYS_DOWN = (pygame.K_DOWN, pygame.K_s)
KEYS_LEFT = (pygame.K_LEFT, pygame.K_a)
KEYS_RIGHT = (pygame.K_RIGHT, pygame.K_d)
KEY_MENU = pygame.K_ESCAPE

DIRS = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
