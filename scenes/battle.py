"""Combattimento a turni in stile JRPG (party fino a 4 vs gruppo nemici)."""
import random

import pygame

from asset_loader import assets
from core import text as T
from core import ui
from core.audio import audio
from core.scene import Scene
from game.enemies import BATTLES
from game.items import ITEMS
from game.skills import SKILLS
from game.stats import compute_damage, heal_amount, make_enemy
from settings import (C_ACCENT, C_ACCENT2, C_EN, C_GOOD, C_HP, C_TEXT,
                      C_TEXT_DIM, C_WARN, ELEMENTS, EN_REGEN_PER_TURN,
                      FLEE_CHANCE, HEIGHT, KEYS_CANCEL, KEYS_CONFIRM,
                      KEYS_LEFT, KEYS_RIGHT, WIDTH)

ANIM_TIME = 0.85
CARD_W, CARD_H = 302, 122


class BattleScene(Scene):
    def __init__(self, game, battle_id):
        super().__init__(game)
        self.battle_id = battle_id
        self.data = BATTLES[battle_id]
        self.party = game.state.members
        self.enemies = []
        counts = {}
        for k in self.data["enemies"]:
            counts[k] = counts.get(k, 0) + 1
        seen = {}
        for k in self.data["enemies"]:
            seen[k] = seen.get(k, 0) + 1
            suffix = f" {chr(64 + seen[k])}" if counts[k] > 1 else ""
            self.enemies.append(make_enemy(k, suffix))
        self.can_flee = self.data.get("flee", True)

        self.phase = "intro"
        self.timer = 0.0
        self.banner = self.data.get("intro", "Nemici in avvicinamento!")
        self.banner_t = 0.0
        self.order = []
        self.turn_i = -1
        self.actor = None
        self.boss_move_i = 0
        self.boss_half_said = False
        self.floats = []
        self.flash = {}
        self.shake = 0.0
        self._fade = None
        self.pending_skill = None      # skill/item in attesa di bersaglio
        self.pending_item = None
        self.target_i = 0
        self.result_lines = []
        self.menu = None
        audio.play_music(self.data.get("music", "battle"))
        audio.sfx("encounter")
        for m in self.party:
            m.guarding = False

    # ------------------------------------------------------------ utilità
    def alive_enemies(self):
        return [e for e in self.enemies if e.alive]

    def alive_party(self):
        return [m for m in self.party if m.alive]

    def _float(self, target, txt, color, size=26):
        x, y = self._pos_of(target)
        self.floats.append(ui.FloatingText(txt, (x, y - 60), color, size))

    def _pos_of(self, c):
        if c.is_player:
            i = self.party.index(c)
            return 20 + i * (CARD_W + 8) + CARD_W // 2, 575 + 30
        alive = self.enemies
        i = alive.index(c)
        n = len(alive)
        cx = WIDTH // 2 + int((i - (n - 1) / 2) * 230)
        return cx, 260

    # -------------------------------------------------------------- turni
    def start_round(self):
        for m in self.alive_party():
            m.restore_en(EN_REGEN_PER_TURN)
        self.order = sorted(self.alive_party() + self.alive_enemies(),
                            key=lambda c: -c.stat("spd"))
        self.turn_i = -1
        self.next_turn()

    def next_turn(self):
        if self.check_end():
            return
        self.turn_i += 1
        if self.turn_i >= len(self.order):
            for c in self.order:
                if c.alive:
                    c.tick_buffs()
            self.start_round()
            return
        self.actor = self.order[self.turn_i]
        if not self.actor.alive:
            self.next_turn()
            return
        self.actor.guarding = False
        if self.actor.is_player:
            self.phase = "menu"
            self.pending_item = None       # mai ereditare selezioni dal turno prima
            self.pending_skill = None
            self.menu = ui.Menu(
                [("Attacca", "attack"), ("Abilità", "skill"),
                 ("Oggetti", "item"), ("Difendi", "guard"), ("Fuggi", "flee")],
                size=26,
                enabled=[True, True, True, True, self.can_flee])
        else:
            self.enemy_act()

    def check_end(self):
        if not self.alive_enemies():
            if self.phase != "victory":
                self.win()
            return True
        if not self.alive_party():
            self.phase = "defeat"
            self.timer = 0.0
            return True
        return False

    def win(self):
        total = sum(e.exp_reward for e in self.enemies)
        self.result_lines = ["VITTORIA!", f"Esperienza guadagnata: {total}"]
        for m in self.party:
            ups = m.gain_exp(total)
            if m.alive:                      # piccolo premio post-battaglia
                m.heal(int(m.max_hp * 0.10))
                m.restore_en(int(m.max_en * 0.25))
            for lv in ups:
                if m.alive:                  # il level-up non rianima i KO
                    m.heal(int(m.max_hp * 0.35))
                self.result_lines.append(f"{m.name} sale al livello {lv}!")
                audio.sfx("levelup")
        self.phase = "victory"
        audio.play_music("victory", loops=0)

    # ---------------------------------------------------------- esecuzione
    def do_attack(self, actor, target, power=100, element=None, name=None):
        dmg, crit, eff = compute_damage(actor, target,
                                        power, element or actor.element)
        target.take_damage(dmg)
        self.flash[id(target)] = 0.30
        col = C_WARN if target.is_player else C_TEXT
        txt = str(dmg)
        if crit:
            txt += "!"
            self.shake = 0.28
            audio.sfx("crit")
        else:
            audio.sfx("hit")
        self._float(target, txt, C_ACCENT2 if crit else col, 30 if crit else 26)
        if eff == "weak":
            self._float(target, "DEBOLE", C_ACCENT2, 18)
        elif eff == "resist":
            self._float(target, "resiste", C_TEXT_DIM, 18)

    def use_skill(self, actor, skill, targets):
        actor.spend_en(skill["cost"])
        kind = skill["kind"]
        audio.sfx("skill")
        if kind in ("attack", "attack_all"):
            for t in targets:
                if t.alive:
                    self.do_attack(actor, t, skill["power"], skill["element"])
            if skill.get("extra_heal"):
                for m in self.alive_party():
                    m.heal(skill["extra_heal"])
                    self._float(m, f"+{skill['extra_heal']}", C_GOOD, 20)
        elif kind in ("heal", "heal_all"):
            for t in targets:
                if t.alive:
                    if skill.get("percent"):
                        base = int(t.max_hp * skill["power"] / 100)
                    else:
                        base = heal_amount(actor, skill["power"])
                    amount = t.heal(base)
                    self._float(t, f"+{amount}", C_GOOD)
            audio.sfx("heal")
        elif kind == "buff":
            actor.add_buff(skill["stat"], skill["mult"], skill["turns"])
            self._float(actor, skill["name"], C_ACCENT, 20)
            audio.sfx("buff")
        elif kind == "buff_party":
            for m in self.alive_party():
                for s in skill["stats"]:
                    m.add_buff(s, skill["mult"], skill["turns"])
                self._float(m, "↑", C_ACCENT, 24)
            audio.sfx("buff")
        elif kind == "debuff":
            for t in targets:
                t.add_buff(skill["stat"], skill["mult"], skill["turns"])
                self._float(t, "↓", (200, 140, 255), 24)
            audio.sfx("buff")
        elif kind == "guard_party":
            for m in self.alive_party():
                m.guarding = True
                self._float(m, "scudo", C_ACCENT, 18)
            audio.sfx("buff")

    def use_item(self, item_id, target):
        it = ITEMS[item_id]
        if not self.game.state.remove_item(item_id):
            return                          # oggetto esaurito: nessun effetto
        audio.sfx("item")
        if it["kind"] == "heal":
            amount = target.heal(it["amount"])
            self._float(target, f"+{amount}", C_GOOD)
        elif it["kind"] == "heal_all":
            for m in self.alive_party():
                m.heal(it["amount"])
                self._float(m, f"+{it['amount']}", C_GOOD, 20)
        elif it["kind"] == "en":
            amount = target.restore_en(it["amount"])
            self._float(target, f"+{amount} EN", C_EN)
        elif it["kind"] == "revive":
            target.hp = max(1, int(target.max_hp * it["amount"]))
            self._float(target, "In piedi!", C_GOOD)

    def enemy_act(self):
        actor = self.actor
        if actor.key == "custode":
            move = actor.moves[self.boss_move_i % len(actor.moves)]
            self.boss_move_i += 1
        else:
            weights = [m.get("w", 1) for m in actor.moves]
            move = random.choices(actor.moves, weights=weights)[0]
        self.banner = f"{actor.name}: {move['name']}"
        self.banner_t = 0.0
        kind = move["kind"]
        if kind == "attack":
            target = random.choice(self.alive_party())
            self.do_attack(actor, target, move["power"], move["element"])
        elif kind == "attack_all":
            for m in list(self.alive_party()):
                self.do_attack(actor, m, move["power"], move["element"])
        elif kind == "debuff":
            target = max(self.alive_party(), key=lambda m: m.stat("atk"))
            target.add_buff(move["stat"], move["mult"], move["turns"])
            self._float(target, "↓", (200, 140, 255), 24)
        if (actor.key == "custode" and not self.boss_half_said
                and actor.hp <= actor.max_hp // 2):
            self.boss_half_said = True
            self.banner = "Il Custode vacilla: «Perché... non volete dormire?»"
            self.banner_t = 0.0
        self.phase = "anim"
        self.timer = 0.0

    def player_execute(self, kind, target=None):
        actor = self.actor
        if kind == "attack":
            self.banner = f"{actor.name}: Attacco"
            self.do_attack(actor, target)
        elif kind == "skill":
            sk = self.pending_skill
            self.banner = f"{actor.name}: {sk['name']}"
            if sk["kind"] in ("attack_all",):
                targets = self.alive_enemies()
            elif sk["kind"] in ("heal_all", "buff_party", "guard_party", "buff"):
                targets = self.alive_party()
            else:
                targets = [target]
            self.use_skill(actor, sk, targets)
        elif kind == "item":
            it = ITEMS[self.pending_item]
            self.banner = f"{actor.name}: {it['name']}"
            self.use_item(self.pending_item, target)
        elif kind == "guard":
            actor.guarding = True
            actor.restore_en(6)
            self.banner = f"{actor.name} si difende"
            self._float(actor, "difesa", C_ACCENT, 18)
        self.banner_t = 0.0
        self.phase = "anim"
        self.timer = 0.0

    # --------------------------------------------------------------- input
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.phase == "intro":
            if event.key in KEYS_CONFIRM:
                self.start_round()
            return
        if self.phase == "victory":
            if event.key in KEYS_CONFIRM:
                self.game.scenes.pop("win")
            return
        if self.phase == "menu":
            res = self.menu.handle_event(event)
            if res == "confirm":
                choice = self.menu.value
                if choice == "attack":
                    self.pending_skill = None
                    self.target_i = 0
                    self.phase = "target_enemy"
                elif choice == "skill":
                    self._open_skill_menu()
                elif choice == "item":
                    self._open_item_menu()
                elif choice == "guard":
                    self.player_execute("guard")
                elif choice == "flee":
                    self._try_flee()
            return
        if self.phase == "skill":
            res = self.menu.handle_event(event)
            if res == "cancel":
                self.phase = "menu"
                self._root_menu()
            elif res == "confirm":
                sk = SKILLS[self.menu.value]
                self.pending_skill = sk
                if sk["kind"] in ("attack_all", "heal_all", "buff",
                                  "buff_party", "guard_party"):
                    self.player_execute("skill")
                elif sk["kind"] == "heal":
                    if sk.get("self_only"):
                        self.player_execute("skill", self.actor)
                    else:
                        self.target_i = 0
                        self.phase = "target_ally"
                else:
                    self.target_i = 0
                    self.phase = "target_enemy"
            return
        if self.phase == "item":
            res = self.menu.handle_event(event)
            if res == "cancel":
                self.phase = "menu"
                self._root_menu()
            elif res == "confirm":
                self.pending_item = self.menu.value
                self.pending_skill = None
                if ITEMS[self.pending_item]["kind"] == "heal_all":
                    self.player_execute("item")
                    self.pending_item = None
                else:
                    self.target_i = 0
                    self.phase = "target_ally"
            return
        if self.phase == "target_enemy":
            targets = self.alive_enemies()
            self._target_input(event, targets, "enemy")
            return
        if self.phase == "target_ally":
            revive = (self.pending_item is not None
                      and ITEMS[self.pending_item]["kind"] == "revive")
            targets = ([m for m in self.party if not m.alive] if revive
                       else self.alive_party())
            if not targets:
                self.phase = "menu"
                self._root_menu()
                return
            self._target_input(event, targets, "ally")
            return

    def _target_input(self, event, targets, side):
        if not targets:
            self.phase = "menu"
            self._root_menu()
            return
        self.target_i %= len(targets)
        if event.key in KEYS_LEFT:
            self.target_i = (self.target_i - 1) % len(targets)
            audio.sfx("move")
        elif event.key in KEYS_RIGHT:
            self.target_i = (self.target_i + 1) % len(targets)
            audio.sfx("move")
        elif event.key in KEYS_CANCEL:
            audio.sfx("cancel")
            if self.pending_item is not None:
                self._open_item_menu()
            elif self.pending_skill is not None:
                self._open_skill_menu()
            else:
                self.phase = "menu"
                self._root_menu()
        elif event.key in KEYS_CONFIRM:
            audio.sfx("confirm")
            target = targets[self.target_i]
            if self.pending_item is not None:
                self.player_execute("item", target)
                self.pending_item = None
            elif self.pending_skill is not None:
                self.player_execute("skill", target)
            else:
                self.player_execute("attack", target)

    def _root_menu(self):
        self.menu = ui.Menu(
            [("Attacca", "attack"), ("Abilità", "skill"),
             ("Oggetti", "item"), ("Difendi", "guard"), ("Fuggi", "flee")],
            size=26,
            enabled=[True, True, True, True, self.can_flee])
        self.pending_item = None
        self.pending_skill = None

    def _open_skill_menu(self):
        actor = self.actor
        items, enabled = [], []
        for sid in actor.skills:
            sk = SKILLS[sid]
            items.append((f"{sk['name']}  ({sk['cost']} EN)", sid))
            enabled.append(actor.en >= sk["cost"])
        if not items:
            return
        self.menu = ui.Menu(items, size=22, enabled=enabled)
        self.pending_item = None
        self.phase = "skill"

    def _open_item_menu(self):
        inv = self.game.state.inventory
        items, enabled = [], []
        for iid, qty in sorted(inv.items()):
            it = ITEMS[iid]
            if it["kind"] == "key":
                continue
            items.append((f"{it['name']} x{qty}", iid))
            enabled.append(True)
        if not items:
            audio.sfx("cancel")
            return
        self.menu = ui.Menu(items, size=22, enabled=enabled)
        self.pending_skill = None
        self.phase = "item"

    def _try_flee(self):
        if random.random() < FLEE_CHANCE:
            audio.sfx("flee")
            self.game.scenes.pop("flee")
        else:
            self.banner = "Fuga fallita!"
            self.banner_t = 0.0
            self.phase = "anim"
            self.timer = 0.0

    # -------------------------------------------------------------- update
    def update(self, dt):
        self.banner_t += dt
        self.floats = [f for f in self.floats if f.update(dt)]
        for k in list(self.flash):
            self.flash[k] -= dt
            if self.flash[k] <= 0:
                del self.flash[k]
        if self.shake > 0:
            self.shake -= dt
        if self.phase == "intro":
            self.timer += dt
            if self.timer > 1.6:
                self.start_round()
        elif self.phase == "anim":
            self.timer += dt
            if self.timer >= ANIM_TIME:
                self.next_turn()
        elif self.phase == "defeat":
            self.timer += dt
            if self.timer > 1.8:
                self.game.scenes.pop("defeat")

    # -------------------------------------------------------------- draw
    def draw(self, surface):
        ox = int(random.uniform(-6, 6) * max(0, self.shake) * 4)
        oy = int(random.uniform(-4, 4) * max(0, self.shake) * 4)
        surface.blit(assets.background(self.data.get("bg", "battle_ship")),
                     (ox, oy))
        self._draw_enemies(surface)
        self._draw_party(surface)
        if self.phase in ("menu", "skill", "item"):
            self._draw_menu(surface)
        if self.phase == "target_enemy":
            self._draw_target_cursor(surface, self.alive_enemies())
        if self.phase == "target_ally":
            revive = (self.pending_item is not None
                      and ITEMS[self.pending_item]["kind"] == "revive")
            targets = ([m for m in self.party if not m.alive] if revive
                       else self.alive_party())
            self._draw_target_cursor(surface, targets)
        for f in self.floats:
            f.draw(surface)
        if self.banner and self.banner_t < 1.6:
            w = assets.font("bold", 26).size(self.banner)[0] + 60
            surface.blit(ui.panel(w, 52), ((WIDTH - w) // 2, 18))
            T.draw(surface, self.banner, (WIDTH // 2, 30), 26,
                   C_TEXT, kind="bold", align="center")
        if self.phase == "victory":
            self._draw_victory(surface)
        if self.phase == "defeat":
            if self._fade is None:
                self._fade = pygame.Surface((WIDTH, HEIGHT))
                self._fade.fill((10, 6, 12))
            self._fade.set_alpha(min(220, int(self.timer * 160)))
            surface.blit(self._fade, (0, 0))
            T.draw(surface, "La squadra è sopraffatta...",
                   (WIDTH // 2, HEIGHT // 2 - 20), 34, C_WARN,
                   kind="bold", align="center")

    def _draw_enemies(self, surface):
        for e in self.enemies:
            if not e.alive:
                continue
            x, y = self._pos_of(e)
            img = assets.enemy_sprite(e.sprite, 160 if e.boss else 110)
            r = img.get_rect(center=(x, y))
            surface.blit(img, r)
            if id(e) in self.flash:
                white = img.copy()
                white.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)
                white.set_alpha(170)
                surface.blit(white, r)
            T.draw(surface, e.name, (x, r.top - 30), 20, C_TEXT, align="center")
            ui.draw_bar(surface, x - 55, r.bottom + 8, 110, 9,
                        e.hp / e.max_hp, C_WARN)
            # debolezze sempre visibili (modalità facile)
            for wi, w in enumerate(e.weak):
                icon = assets.ui(ELEMENTS[w]["icon"], (22, 22))
                surface.blit(icon, (x - 11 * len(e.weak) + wi * 24, r.bottom + 22))

    def _draw_party(self, surface):
        for i, m in enumerate(self.party):
            x = 20 + i * (CARD_W + 8)
            y = HEIGHT - CARD_H - 14
            surface.blit(ui.panel(CARD_W, CARD_H), (x, y))
            if m is self.actor and self.phase in ("menu", "skill", "item",
                                                  "target_enemy", "target_ally"):
                pygame.draw.rect(surface, C_ACCENT, (x, y, CARD_W, CARD_H),
                                 2, border_radius=10)
            por = assets.portrait(m.key, 72)
            if not m.alive:
                por = por.copy()
                por.set_alpha(80)
            surface.blit(por, (x + 12, y + 24))
            name_col = C_TEXT if m.alive else C_TEXT_DIM
            T.draw(surface, f"{m.name}  Lv.{m.level}", (x + 96, y + 12), 20,
                   name_col, kind="bold")
            ui.draw_bar(surface, x + 96, y + 44, 186, 12, m.hp / m.max_hp, C_HP)
            T.draw(surface, f"{m.hp}/{m.max_hp}", (x + 96 + 186, y + 38), 16,
                   C_TEXT_DIM, align="right")
            ui.draw_bar(surface, x + 96, y + 74, 186, 9, m.en / m.max_en, C_EN)
            T.draw(surface, f"{m.en}/{m.max_en} EN", (x + 96 + 186, y + 84), 15,
                   C_TEXT_DIM, align="right")
            if m.guarding:
                pygame.draw.rect(surface, C_ACCENT, (x + 4, y + 4,
                                                     CARD_W - 8, 4),
                                 border_radius=2)
            if id(m) in self.flash:
                hl = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
                hl.fill((255, 80, 80, 70))
                surface.blit(hl, (x, y))

    def _draw_menu(self, surface):
        n = len(self.menu.items)
        h = n * 40 + 30
        w = 420 if self.phase != "menu" else 240
        x = WIDTH - w - 24
        y = HEIGHT - CARD_H - h - 26
        surface.blit(ui.panel(w, h), (x, y))
        self.menu.draw(surface, x + 44, y + 18, 40)
        # descrizione abilità/oggetto selezionato
        desc = None
        if self.phase == "skill":
            desc = SKILLS[self.menu.value]["desc"]
        elif self.phase == "item":
            desc = ITEMS[self.menu.value]["desc"]
        if desc:
            surface.blit(ui.panel(560, 58), (x - 570, y + h - 58))
            for li, line in enumerate(T.wrap(desc, 18, 520)[:2]):
                T.draw(surface, line, (x - 545, y + h - 48 + li * 24), 18,
                       C_TEXT_DIM)

    def _draw_target_cursor(self, surface, targets):
        if not targets:
            return
        self.target_i %= len(targets)
        t = targets[self.target_i]
        x, y = self._pos_of(t)
        top = y - (90 if not t.is_player else 75)
        pygame.draw.polygon(surface, C_ACCENT2,
                            [(x - 12, top - 18), (x + 12, top - 18), (x, top)])
        T.draw(surface, t.name, (x, top - 44), 20, C_ACCENT2,
               kind="bold", align="center")

    def _draw_victory(self, surface):
        w, h = 620, 120 + 30 * len(self.result_lines)
        x, y = (WIDTH - w) // 2, (HEIGHT - h) // 2 - 40
        surface.blit(ui.panel(w, h), (x, y))
        T.draw(surface, self.result_lines[0], (x + w // 2, y + 24), 34,
               C_ACCENT2, kind="title", align="center")
        for i, line in enumerate(self.result_lines[1:]):
            T.draw(surface, line, (x + w // 2, y + 84 + i * 30), 22,
                   C_TEXT, align="center")
        T.draw(surface, "SPAZIO per continuare", (x + w // 2, y + h - 34), 18,
               C_TEXT_DIM, align="center")
