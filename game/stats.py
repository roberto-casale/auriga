"""Combattenti, formula del danno, crescita di livello."""
import random

from game.enemies import ENEMIES
from game.skills import skills_for
from settings import CRIT_CHANCE, CRIT_MULT, RESIST_MULT, WEAK_MULT

STAT_NAMES = ("hp", "en", "atk", "dfs", "spd")

# base e crescita per livello dei membri del party
PARTY_DEFS = {
    "kaira": {
        "name": "Kaira", "full": "Kaira Volpe", "epithet": "Capitano ad interim",
        "element": "cinetico", "weak": [], "resist": ["cinetico"],
        "base": {"hp": 120, "en": 30, "atk": 14, "dfs": 12, "spd": 9},
        "growth": {"hp": 12, "en": 3, "atk": 2.2, "dfs": 1.8, "spd": 1.0}},
    "ilan": {
        "name": "Ilan", "full": "Dr. Ilan Reyes", "epithet": "Xenolinguista",
        "element": "ionico", "weak": [], "resist": [],
        "base": {"hp": 95, "en": 40, "atk": 10, "dfs": 9, "spd": 10},
        "growth": {"hp": 9, "en": 4, "atk": 1.6, "dfs": 1.4, "spd": 1.2}},
    "sette": {
        "name": "Sette", "full": "SEV-7 «Sette»", "epithet": "Androide risvegliato",
        "element": "ionico", "weak": [], "resist": ["ionico"],
        "base": {"hp": 100, "en": 36, "atk": 15, "dfs": 9, "spd": 13},
        "growth": {"hp": 10, "en": 3.5, "atk": 2.4, "dfs": 1.4, "spd": 1.6}},
    "naia": {
        "name": "Naia", "full": "Naia Sorel", "epithet": "Botanica di bordo",
        "element": "bio", "weak": [], "resist": ["bio"],
        "base": {"hp": 90, "en": 42, "atk": 11, "dfs": 8, "spd": 11},
        "growth": {"hp": 9, "en": 4.2, "atk": 1.8, "dfs": 1.3, "spd": 1.4}},
}

LEVEL_CAP = 10


def exp_to_next(level):
    return int(40 + 28 * level ** 1.5)


class Combatant:
    def __init__(self, key, name, base, element, weak, resist, is_player):
        self.key = key
        self.name = name
        self.base = dict(base)
        self.element = element
        self.weak = list(weak)
        self.resist = list(resist)
        self.is_player = is_player
        self.hp = self.max_hp
        self.en = self.max_en
        self.buffs = []            # {"stat","mult","turns"}
        self.guarding = False

    # --------------------------------------------------------------- stat
    @property
    def max_hp(self):
        return int(self.base["hp"])

    @property
    def max_en(self):
        return int(self.base["en"])

    def stat(self, name):
        v = self.base[name]
        for b in self.buffs:
            if b["stat"] == name:
                v *= b["mult"]
        return v

    @property
    def alive(self):
        return self.hp > 0

    # ------------------------------------------------------------- azioni
    def take_damage(self, dmg):
        self.hp = max(0, self.hp - int(dmg))
        if self.hp == 0:
            self.buffs = []
            self.guarding = False

    def heal(self, amount):
        before = self.hp
        self.hp = min(self.max_hp, self.hp + int(amount))
        return self.hp - before

    def restore_en(self, amount):
        before = self.en
        self.en = min(self.max_en, self.en + int(amount))
        return self.en - before

    def spend_en(self, amount):
        self.en = max(0, self.en - int(amount))

    def add_buff(self, stat, mult, turns):
        # un buff per stat: il nuovo sostituisce il vecchio
        self.buffs = [b for b in self.buffs if b["stat"] != stat]
        self.buffs.append({"stat": stat, "mult": mult, "turns": turns})

    def tick_buffs(self):
        for b in self.buffs:
            b["turns"] -= 1
        self.buffs = [b for b in self.buffs if b["turns"] > 0]


class PartyMember(Combatant):
    def __init__(self, key, level=1):
        d = PARTY_DEFS[key]
        base = {s: d["base"][s] + d["growth"][s] * (level - 1) for s in STAT_NAMES}
        super().__init__(key, d["name"], base, d["element"], d["weak"], d["resist"], True)
        self.full_name = d["full"]
        self.epithet = d["epithet"]
        self.level = level
        self.exp = 0
        self.skills = skills_for(key, level)

    def recompute(self):
        d = PARTY_DEFS[self.key]
        self.base = {s: d["base"][s] + d["growth"][s] * (self.level - 1) for s in STAT_NAMES}
        self.skills = skills_for(self.key, self.level)

    def gain_exp(self, amount):
        """Ritorna la lista dei livelli raggiunti (per il log di battaglia)."""
        ups = []
        if not self.alive:            # anche i KO imparano qualcosa (facile)
            amount = amount // 2
        self.exp += amount
        while self.level < LEVEL_CAP and self.exp >= exp_to_next(self.level):
            self.exp -= exp_to_next(self.level)
            self.level += 1
            self.recompute()
            ups.append(self.level)
        return ups


def make_enemy(key, suffix=""):
    d = ENEMIES[key]
    e = Combatant(key, d["name"] + suffix,
                  {s: d[s] for s in STAT_NAMES},
                  "cinetico", d["weak"], d["resist"], False)
    e.sprite = d["sprite"]
    e.moves = d["moves"]
    e.exp_reward = d["exp"]
    e.boss = d.get("boss", False)
    return e


def compute_damage(attacker, defender, power, element, can_crit=True):
    """Ritorna (danno, crit: bool, eff: 'weak'|'resist'|None)."""
    base = attacker.stat("atk") * 2 * power / 100.0
    eff = None
    if element in defender.weak:
        base *= WEAK_MULT
        eff = "weak"
    elif element in defender.resist:
        base *= RESIST_MULT
        eff = "resist"
    base *= 100.0 / (100.0 + defender.stat("dfs") * 4)
    base *= random.uniform(0.88, 1.12)
    crit = can_crit and attacker.is_player and random.random() < CRIT_CHANCE
    if crit:
        base *= CRIT_MULT
    if defender.guarding:
        base *= 0.5
    return max(1, int(base)), crit, eff


def heal_amount(caster, power):
    return int(power * (1 + 0.06 * (getattr(caster, "level", 1) - 1)))
