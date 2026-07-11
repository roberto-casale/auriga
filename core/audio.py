"""Gestione musica ed effetti, tollerante all'assenza del mixer (test headless)."""
import sys

import pygame

from asset_loader import assets

IS_WEB = sys.platform == "emscripten"


class Audio:
    def __init__(self):
        self.ok = False
        self.music_vol = 0.7
        self.sfx_vol = 0.8
        self.current = None

    def init(self):
        try:
            # In WASM il buffer piccolo va in underrun sul main thread
            # (crepitii/fruscii): sul web serve un buffer molto più largo.
            buffer = 4096 if IS_WEB else 512
            # pygame.init() (chiamato prima in main.py) apre già il mixer coi
            # default: pre_init a quel punto è ignorato. Per applicare davvero
            # freq/buffer bisogna chiuderlo e riaprirlo con parametri espliciti.
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.init(44100, -16, 2, buffer)
            self.ok = True
        except pygame.error:
            self.ok = False
        assets.sfx_enabled = self.ok
        return self.ok

    # ------------------------------------------------------------ musica
    def play_music(self, name, loops=-1, fade_ms=600):
        if not self.ok or name == self.current:
            return
        path = assets.music_path(name)
        if path is None:
            self.current = name          # evita retry a ogni frame
            return
        try:
            # In WASM (pygbag) music.load() con un'altra traccia ancora in
            # riproduzione (anche in fadeout) blocca il main thread per
            # sempre: fermare e scaricare SEMPRE prima di caricare.
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except (pygame.error, AttributeError):
                pass
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_vol)
            pygame.mixer.music.play(loops, fade_ms=0 if IS_WEB else fade_ms)
            self.current = name
        except pygame.error:
            self.current = name

    def stop_music(self, fade_ms=500):
        if self.ok:
            try:
                if IS_WEB:
                    pygame.mixer.music.stop()     # niente fadeout in WASM
                else:
                    pygame.mixer.music.fadeout(fade_ms)
            except pygame.error:
                pass
        self.current = None

    def set_music_vol(self, v):
        self.music_vol = max(0.0, min(1.0, v))
        if self.ok:
            try:
                pygame.mixer.music.set_volume(self.music_vol)
            except pygame.error:
                pass

    # --------------------------------------------------------------- sfx
    def sfx(self, name):
        if not self.ok:
            return
        snd = assets.sfx(name)
        if snd is not None:
            snd.set_volume(self.sfx_vol)
            snd.play()

    def set_sfx_vol(self, v):
        self.sfx_vol = max(0.0, min(1.0, v))


audio = Audio()
