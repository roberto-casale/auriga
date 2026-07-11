"""Definizione abilità del party e tabella di apprendimento."""

# kind: attack | attack_all | heal | heal_all | buff | buff_party | debuff |
#       guard_party | revive
SKILLS = {
    # ------------------------------------------------------------- Kaira
    "colpo_chiave": {
        "name": "Colpo di Chiave", "cost": 6, "power": 135, "element": "cinetico",
        "kind": "attack", "desc": "Un colpo secco con la chiave dinamometrica."},
    "muro_di_ferro": {
        "name": "Muro di Ferro", "cost": 8, "power": 0, "element": "cinetico",
        "kind": "guard_party", "turns": 1,
        "desc": "Kaira fa scudo: il party subisce danni dimezzati per un turno."},
    "sovraccarico": {
        "name": "Sovraccarico", "cost": 13, "power": 100, "element": "cinetico",
        "kind": "attack_all", "desc": "Onda d'urto che colpisce tutti i nemici."},
    "riparazione": {
        "name": "Riparazione d'Emergenza", "cost": 10, "power": 45, "element": "cinetico",
        "kind": "heal", "self_only": True, "percent": True,
        "desc": "Kaira si rattoppa da sola: recupera il 45% degli HP."},

    # -------------------------------------------------------------- Ilan
    "impacco": {
        "name": "Impacco Medicale", "cost": 7, "power": 55, "element": "bio",
        "kind": "heal", "desc": "Cura un alleato con un gel rigenerante."},
    "analisi": {
        "name": "Analisi", "cost": 5, "power": 0, "element": "ionico",
        "kind": "debuff", "stat": "dfs", "mult": 0.7, "turns": 3,
        "desc": "Studia il nemico: la sua difesa cala del 30% per 3 turni."},
    "coro_calmo": {
        "name": "Parole che Curano", "cost": 14, "power": 34, "element": "bio",
        "kind": "heal_all", "desc": "La voce di Ilan rincuora tutto il party."},
    "lancia_ionica": {
        "name": "Lancia Ionica", "cost": 6, "power": 125, "element": "ionico",
        "kind": "attack", "desc": "Un dardo di plasma dallo scanner modificato."},

    # ------------------------------------------------------------- Sette
    "scarica": {
        "name": "Scarica", "cost": 6, "power": 135, "element": "ionico",
        "kind": "attack", "desc": "Arco voltaico dal palmo di SEV-7."},
    "lama_termica": {
        "name": "Lama Termica", "cost": 6, "power": 135, "element": "termico",
        "kind": "attack", "desc": "Una lama di calore bianco."},
    "protocollo_assalto": {
        "name": "Protocollo d'Assalto", "cost": 8, "power": 0, "element": "ionico",
        "kind": "buff", "stat": "atk", "mult": 1.4, "turns": 3,
        "desc": "Sette riconfigura i servomotori: +40% attacco per 3 turni."},
    "emp": {
        "name": "Impulso EMP", "cost": 14, "power": 110, "element": "ionico",
        "kind": "attack_all", "desc": "Impulso elettromagnetico su tutti i nemici."},

    # -------------------------------------------------------------- Naia
    "rovi_luminosi": {
        "name": "Rovi Luminosi", "cost": 6, "power": 130, "element": "bio",
        "kind": "attack", "desc": "Radici bioluminescenti stringono il nemico."},
    "spora_lenitiva": {
        "name": "Spora Lenitiva", "cost": 7, "power": 60, "element": "bio",
        "kind": "heal", "desc": "Un soffio di spore che richiude le ferite."},
    "polline": {
        "name": "Polline Vivace", "cost": 12, "power": 0, "element": "bio",
        "kind": "buff_party", "stats": ["atk", "spd"], "mult": 1.2, "turns": 2,
        "desc": "Il party respira coraggio: +20% attacco e velocità, 2 turni."},
    "fioritura": {
        "name": "Fioritura", "cost": 16, "power": 115, "element": "bio",
        "kind": "attack_all", "extra_heal": 25,
        "desc": "Un giardino esplode in battaglia: danni a tutti e lieve cura."},
}

# livello -> abilità imparate
LEARN = {
    "kaira": {1: ["colpo_chiave", "muro_di_ferro"], 3: ["sovraccarico"], 5: ["riparazione"]},
    "ilan":  {1: ["impacco", "analisi", "lancia_ionica"], 3: ["coro_calmo"]},
    "sette": {1: ["scarica", "lama_termica"], 3: ["protocollo_assalto"], 5: ["emp"]},
    "naia":  {1: ["rovi_luminosi", "spora_lenitiva"], 3: ["polline"], 5: ["fioritura"]},
}


def skills_for(key, level):
    out = []
    for lv in sorted(LEARN.get(key, {})):
        if lv <= level:
            out.extend(LEARN[key][lv])
    return out
