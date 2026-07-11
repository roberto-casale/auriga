"""Menu di pausa (stato, zaino, opzioni) e schermata slot di salvataggio."""
import pygame

from asset_loader import assets
from core import text as T
from core import ui
from core.audio import audio
from core.scene import Scene
from game.items import ITEMS
from game.save import all_slots, load_slot, save_slot
from game.skills import SKILLS
from game.stats import exp_to_next
from settings import (C_ACCENT, C_ACCENT2, C_EN, C_GOOD, C_HP, C_TEXT,
                      C_TEXT_DIM, C_XP, ELEMENTS, HEIGHT, KEYS_CANCEL,
                      KEYS_CONFIRM, KEYS_LEFT, KEYS_RIGHT, SAVE_SLOTS, WIDTH)


class PauseMenuScene(Scene):
    overlay = True

    def __init__(self, game):
        super().__init__(game)
        self.mode = "root"
        self.menu = self._root_menu()
        self.sub = None
        self.msg = ""
        self.msg_t = 0.0

    def _root_menu(self):
        return ui.Menu([("Riprendi", "resume"), ("Stato", "status"),
                        ("Zaino", "items"), ("Salva", "save"),
                        ("Opzioni", "options"), ("Torna al titolo", "title")],
                       size=26)

    # ------------------------------------------------------------- input
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.mode == "root":
            res = self.menu.handle_event(event)
            if res == "cancel":
                self.game.scenes.pop(None)
            elif res == "confirm":
                v = self.menu.value
                if v == "resume":
                    self.game.scenes.pop(None)
                elif v == "status":
                    self.mode = "status"
                elif v == "items":
                    self._open_items()
                elif v == "save":
                    self.game.scenes.push(SaveMenuScene(self.game, "save"))
                elif v == "options":
                    self.mode = "options"
                    self.sub = ui.Menu([("Musica", "music"), ("Effetti", "sfx")],
                                       size=26)
                elif v == "title":
                    from scenes.title import TitleScene
                    audio.stop_music()
                    self.game.scenes.clear_to(TitleScene(self.game))
        elif self.mode == "status":
            if event.key in KEYS_CANCEL or event.key in KEYS_CONFIRM:
                audio.sfx("cancel")
                self.mode = "root"
        elif self.mode == "items":
            res = self.sub.handle_event(event)
            if res == "cancel":
                self.mode = "root"
            elif res == "confirm":
                iid = self.sub.value
                if ITEMS[iid]["kind"] in ("heal", "en", "revive"):
                    self.mode = "items_target"
                    self.target = ui.Menu(
                        [(m.name, m.key) for m in self.game.state.members],
                        size=24)
                else:
                    self._use_item(iid, None)
        elif self.mode == "items_target":
            res = self.target.handle_event(event)
            if res == "cancel":
                self.mode = "items"
            elif res == "confirm":
                self._use_item(self.sub.value, self.target.value)
        elif self.mode == "options":
            res = self.sub.handle_event(event)
            if res == "cancel":
                self.mode = "root"
            elif event.key in KEYS_LEFT or event.key in KEYS_RIGHT:
                delta = -0.1 if event.key in KEYS_LEFT else 0.1
                if self.sub.value == "music":
                    audio.set_music_vol(audio.music_vol + delta)
                else:
                    audio.set_sfx_vol(audio.sfx_vol + delta)
                    audio.sfx("move")

    def _open_items(self):
        st = self.game.state
        entries = []
        for iid, qty in sorted(st.inventory.items()):
            it = ITEMS[iid]
            label = f"{it['name']} x{qty}" if it["kind"] != "key" else it["name"]
            entries.append((label, iid))
        if not entries:
            self.msg, self.msg_t = "Lo zaino è vuoto.", 0.0
            return
        self.sub = ui.Menu(entries, size=22)
        self.mode = "items"

    def _use_item(self, iid, member_key):
        st = self.game.state
        it = ITEMS[iid]
        if it["kind"] == "key":
            self.msg, self.msg_t = it["desc"], 0.0
            return
        m = st.member(member_key) if member_key else None
        used = False
        if it["kind"] == "heal" and m and m.alive and m.hp < m.max_hp:
            m.heal(it["amount"])
            used = True
        elif it["kind"] == "en" and m and m.alive and m.en < m.max_en:
            m.restore_en(it["amount"])
            used = True
        elif it["kind"] == "revive" and m and not m.alive:
            m.hp = max(1, int(m.max_hp * it["amount"]))
            used = True
        elif it["kind"] == "heal_all":
            for mm in st.alive_members():
                mm.heal(it["amount"])
            used = True
        if used:
            st.remove_item(iid)
            audio.sfx("heal")
            self.msg, self.msg_t = f"{it['name']} usato.", 0.0
        else:
            audio.sfx("cancel")
            self.msg, self.msg_t = "Non avrebbe effetto.", 0.0
        if st.inventory:
            self._open_items()
            self.mode = "items"
        else:
            self.mode = "root"

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.msg_t += dt

    # ------------------------------------------------------------- draw
    def draw(self, surface):
        surface.blit(ui.veil((6, 8, 14, 150)), (0, 0))
        if self.mode in ("root",):
            w, h = 320, 320
            x, y = 60, 120
            surface.blit(ui.panel(w, h), (x, y))
            T.draw(surface, "PAUSA", (x + 24, y + 16), 28, C_ACCENT2, kind="title")
            self.menu.draw(surface, x + 64, y + 70, 40)
            T.draw(surface, self.game.state.act, (60, 70), 22, C_TEXT_DIM)
        elif self.mode == "status":
            self._draw_status(surface)
        elif self.mode in ("items", "items_target"):
            w, h = 620, 420
            x, y = 100, 120
            surface.blit(ui.panel(w, h), (x, y))
            T.draw(surface, "ZAINO", (x + 24, y + 16), 28, C_ACCENT2, kind="title")
            self.sub.draw(surface, x + 64, y + 70, 36)
            iid = self.sub.value
            if iid:
                for li, line in enumerate(T.wrap(ITEMS[iid]["desc"], 20, w - 60)[:2]):
                    T.draw(surface, line, (x + 30, y + h - 64 + li * 24), 20,
                           C_TEXT_DIM)
            if self.mode == "items_target":
                tw, th = 260, 60 + 36 * len(self.target.items)
                tx, ty = x + w + 16, y + 40
                surface.blit(ui.panel(tw, th), (tx, ty))
                T.draw(surface, "Su chi?", (tx + 20, ty + 12), 20, C_TEXT_DIM)
                self.target.draw(surface, tx + 48, ty + 44, 36)
        elif self.mode == "options":
            w, h = 460, 220
            x, y = 100, 140
            surface.blit(ui.panel(w, h), (x, y))
            T.draw(surface, "OPZIONI", (x + 24, y + 16), 28, C_ACCENT2, kind="title")
            self.sub.draw(surface, x + 64, y + 76, 48)
            for i, vol in enumerate((audio.music_vol, audio.sfx_vol)):
                ui.draw_bar(surface, x + 220, y + 84 + i * 48, 180, 12, vol,
                            C_ACCENT)
            T.draw(surface, "Frecce sinistra/destra per regolare",
                   (x + 24, y + h - 36), 18, C_TEXT_DIM)
        if self.msg and self.msg_t < 2.0:
            w = assets.font("text", 22).size(self.msg)[0] + 50
            surface.blit(ui.panel(w, 46), ((WIDTH - w) // 2, HEIGHT - 80))
            T.draw(surface, self.msg, (WIDTH // 2, HEIGHT - 70), 22,
                   C_TEXT, align="center")

    def _draw_status(self, surface):
        st = self.game.state
        surface.blit(ui.panel(1160, 560), (60, 80))
        T.draw(surface, "STATO DELLA SQUADRA", (90, 100), 28, C_ACCENT2,
               kind="title")
        for i, m in enumerate(st.members):
            x = 90 + (i % 2) * 570
            y = 150 + (i // 2) * 240
            surface.blit(ui.panel(540, 224), (x, y))
            surface.blit(assets.portrait(m.key, 110), (x + 16, y + 16))
            T.draw(surface, f"{m.full_name}", (x + 140, y + 14), 24, C_TEXT,
                   kind="bold")
            T.draw(surface, f"{m.epithet} — Lv.{m.level}", (x + 140, y + 44),
                   19, C_TEXT_DIM)
            el = ELEMENTS[m.element]
            T.draw(surface, el["name"], (x + 140, y + 68), 18, el["color"])
            ui.draw_bar(surface, x + 140, y + 96, 220, 12, m.hp / m.max_hp, C_HP)
            T.draw(surface, f"HP {m.hp}/{m.max_hp}", (x + 372, y + 90), 17,
                   C_TEXT_DIM)
            ui.draw_bar(surface, x + 140, y + 118, 220, 10, m.en / m.max_en, C_EN)
            T.draw(surface, f"EN {m.en}/{m.max_en}", (x + 372, y + 112), 17,
                   C_TEXT_DIM)
            nxt = exp_to_next(m.level)
            ui.draw_bar(surface, x + 140, y + 140, 220, 8,
                        m.exp / max(1, nxt), C_XP)
            T.draw(surface, f"EXP {m.exp}/{nxt}", (x + 372, y + 132), 17,
                   C_TEXT_DIM)
            stats = (f"ATK {int(m.stat('atk'))}   DIF {int(m.stat('dfs'))}"
                     f"   VEL {int(m.stat('spd'))}")
            T.draw(surface, stats, (x + 16, y + 152), 19, C_TEXT)
            skill_names = ", ".join(SKILLS[sid]["name"] for sid in m.skills)
            for li, line in enumerate(T.wrap("Abilità: " + skill_names, 17,
                                             500)[:2]):
                T.draw(surface, line, (x + 16, y + 178 + li * 22), 17,
                       C_TEXT_DIM)


class SaveMenuScene(Scene):
    overlay = True

    def __init__(self, game, mode):
        super().__init__(game)
        self.mode = mode                    # "save" | "load"
        self.infos = all_slots()
        self.menu = ui.Menu([(f"Slot {n}", n) for n in range(1, SAVE_SLOTS + 1)],
                            size=26)
        self.msg = ""
        self.msg_t = 0.0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        res = self.menu.handle_event(event)
        if res == "cancel":
            self.game.scenes.pop(None)
        elif res == "confirm":
            n = self.menu.value
            if self.mode == "save":
                save_slot(n, self.game.state)
                self.infos = all_slots()
                audio.sfx("save")
                self.msg, self.msg_t = "Partita salvata.", 0.0
            else:
                st = load_slot(n)
                if st is None:
                    audio.sfx("cancel")
                    self.msg, self.msg_t = "Slot vuoto.", 0.0
                else:
                    self.game.state = st
                    from scenes.explore import ExploreScene
                    audio.stop_music()
                    self.game.scenes.clear_to(ExploreScene(self.game))

    def update(self, dt):
        self.msg_t += dt

    def draw(self, surface):
        surface.blit(ui.veil((6, 8, 14, 160)), (0, 0))
        w, h = 760, 380
        x, y = (WIDTH - w) // 2, 140
        surface.blit(ui.panel(w, h), (x, y))
        title = "SALVA PARTITA" if self.mode == "save" else "CARICA PARTITA"
        T.draw(surface, title, (x + w // 2, y + 20), 30, C_ACCENT2,
               kind="title", align="center")
        for i, n in enumerate(range(1, SAVE_SLOTS + 1)):
            sy = y + 80 + i * 88
            info = self.infos.get(n)
            selected = self.menu.index == i
            box = ui.panel(w - 120, 78)
            surface.blit(box, (x + 60, sy))
            if selected:
                pygame.draw.rect(surface, C_ACCENT, (x + 60, sy, w - 120, 78),
                                 2, border_radius=10)
            T.draw(surface, f"Slot {n}", (x + 84, sy + 10), 24,
                   C_ACCENT if selected else C_TEXT, kind="bold")
            if info:
                T.draw(surface, info["act"], (x + 84, sy + 42), 19, C_TEXT_DIM)
                T.draw(surface, f"Lv.{info['level']} — {info['party']}",
                       (x + 330, sy + 10), 19, C_TEXT_DIM)
                T.draw(surface, info["time"], (x + w - 160, sy + 42), 19,
                       C_TEXT_DIM)
            else:
                T.draw(surface, "— vuoto —", (x + 330, sy + 26), 19, C_TEXT_DIM)
        if self.msg and self.msg_t < 2.0:
            T.draw(surface, self.msg, (x + w // 2, y + h - 40), 20, C_GOOD,
                   align="center")
