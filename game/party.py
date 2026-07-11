"""Stato di gioco persistente: party, inventario, flag, posizione."""
from game.items import ITEMS
from game.stats import PartyMember
from settings import MAX_ITEM_STACK, MAX_PARTY


class GameState:
    def __init__(self):
        self.members = []
        self.inventory = {}            # item_id -> qty
        self.flags = {}                # nome -> valore
        self.affinity = {"kaira_ilan": 0, "naia_sette": 0}
        self.map_id = "habitat"
        self.px, self.py = 5, 6
        self.facing = "down"
        self.checkpoint = ("habitat", 5, 6)
        self.done = set()              # trigger/eventi una-tantum consumati
        self.playtime = 0.0
        self.act = "Atto I — Il Ponte Habitat"

    # ------------------------------------------------------------- party
    def add_member(self, key, level=1):
        if not self.has_member(key) and len(self.members) < MAX_PARTY:
            m = PartyMember(key, level)
            # i nuovi arrivati entrano al livello del veterano più alto
            top = max([x.level for x in self.members], default=level)
            if top > level:
                m.level = top
                m.recompute()
                m.hp, m.en = m.max_hp, m.max_en
            self.members.append(m)

    def has_member(self, key):
        return any(m.key == key for m in self.members)

    def member(self, key):
        for m in self.members:
            if m.key == key:
                return m
        return None

    def alive_members(self):
        return [m for m in self.members if m.alive]

    def full_heal(self):
        for m in self.members:
            m.hp, m.en = m.max_hp, m.max_en
            m.buffs = []
            m.guarding = False

    # ---------------------------------------------------------- oggetti
    def add_item(self, item_id, qty=1):
        if item_id not in ITEMS:
            return
        cap = 99 if ITEMS[item_id]["kind"] == "key" else MAX_ITEM_STACK
        self.inventory[item_id] = min(cap, self.inventory.get(item_id, 0) + qty)

    def remove_item(self, item_id, qty=1):
        if self.inventory.get(item_id, 0) >= qty:
            self.inventory[item_id] -= qty
            if self.inventory[item_id] <= 0:
                del self.inventory[item_id]
            return True
        return False

    def has_item(self, item_id):
        return self.inventory.get(item_id, 0) > 0

    # -------------------------------------------------------------- flag
    def set_flag(self, name, value=True):
        self.flags[name] = value

    def flag(self, name, default=False):
        return self.flags.get(name, default)

    # ------------------------------------------------------ salvataggio
    def to_dict(self):
        return {
            "members": [{
                "key": m.key, "level": m.level, "exp": m.exp,
                "hp": m.hp, "en": m.en,
            } for m in self.members],
            "inventory": dict(self.inventory),
            "flags": dict(self.flags),
            "affinity": dict(self.affinity),
            "map_id": self.map_id, "px": self.px, "py": self.py,
            "facing": self.facing,
            "checkpoint": list(self.checkpoint),
            "done": sorted(self.done),
            "playtime": round(self.playtime, 1),
            "act": self.act,
        }

    @classmethod
    def from_dict(cls, data):
        from world.mapdata import MAPS
        st = cls()
        st.members = []
        for md in data.get("members", []):
            m = PartyMember(md["key"], md.get("level", 1))
            m.exp = md.get("exp", 0)
            # hp=0 (KO) va preservato: rianimare al load falserebbe lo stato
            m.hp = max(0, min(m.max_hp, md.get("hp", m.max_hp)))
            m.en = max(0, min(m.max_en, md.get("en", m.max_en)))
            st.members.append(m)
        if st.members and all(m.hp == 0 for m in st.members):
            st.members[0].hp = 1           # salvagente: mai un party tutto KO
        st.inventory = {k: v for k, v in data.get("inventory", {}).items() if k in ITEMS}
        st.flags = dict(data.get("flags", {}))
        st.affinity.update(data.get("affinity", {}))
        st.map_id = data.get("map_id", "habitat")
        st.px, st.py = int(data.get("px", 5)), int(data.get("py", 6))
        st.facing = data.get("facing", "down")
        cp = data.get("checkpoint", ["habitat", 5, 6])
        st.checkpoint = (cp[0], int(cp[1]), int(cp[2]))
        # uno slot corrotto deve fallire QUI (load_slot lo intercetta),
        # non con un KeyError a gioco avviato
        if st.map_id not in MAPS or st.checkpoint[0] not in MAPS:
            raise ValueError(f"mappa sconosciuta nel salvataggio: {st.map_id}")
        rows = MAPS[st.map_id]["rows"]
        if not (0 <= st.py < len(rows) and 0 <= st.px < max(len(r) for r in rows)):
            raise ValueError("posizione fuori mappa nel salvataggio")
        st.done = set(data.get("done", []))
        st.playtime = float(data.get("playtime", 0.0))
        st.act = data.get("act", st.act)
        return st


def new_game_state():
    st = GameState()
    st.add_member("kaira")
    st.add_item("razione", 3)
    st.add_item("cella", 2)
    return st
