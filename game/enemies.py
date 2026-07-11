"""Nemici e composizione delle battaglie."""

# Le mosse dei nemici sono definite inline: {name, power, element, kind}
# kind: attack | attack_all | debuff
ENEMIES = {
    "drone_a": {
        "name": "Drone Impazzito", "sprite": "enemy_drone_a",
        "hp": 42, "en": 20, "atk": 8, "dfs": 5, "spd": 8,
        "weak": ["ionico"], "resist": ["cinetico"], "exp": 24,
        "moves": [
            {"name": "Artiglio Servo", "power": 100, "element": "cinetico", "kind": "attack", "w": 7},
            {"name": "Mini Laser", "power": 115, "element": "termico", "kind": "attack", "w": 3},
        ]},
    "drone_b": {
        "name": "Drone Saldatore", "sprite": "enemy_drone_b",
        "hp": 58, "en": 24, "atk": 10, "dfs": 6, "spd": 6,
        "weak": ["ionico"], "resist": [], "exp": 32,
        "moves": [
            {"name": "Fiamma Ossidrica", "power": 110, "element": "termico", "kind": "attack", "w": 6},
            {"name": "Scintille", "power": 80, "element": "termico", "kind": "attack_all", "w": 2},
            {"name": "Colpo di Braccio", "power": 100, "element": "cinetico", "kind": "attack", "w": 4},
        ]},
    "spora": {
        "name": "Spora d'Ombra", "sprite": "enemy_spora",
        "hp": 52, "en": 20, "atk": 9, "dfs": 4, "spd": 10,
        "weak": ["termico"], "resist": ["bio"], "exp": 28,
        "moves": [
            {"name": "Sbuffo Tossico", "power": 100, "element": "bio", "kind": "attack", "w": 7},
            {"name": "Nube Amara", "power": 70, "element": "bio", "kind": "attack_all", "w": 3},
        ]},
    "ombra": {
        "name": "Frammento d'Ombra", "sprite": "enemy_ombra",
        "hp": 74, "en": 26, "atk": 11, "dfs": 7, "spd": 11,
        "weak": ["bio"], "resist": ["ionico"], "exp": 42,
        "moves": [
            {"name": "Artiglio Statico", "power": 110, "element": "ionico", "kind": "attack", "w": 6},
            {"name": "Sussurro Freddo", "power": 0, "element": "ionico", "kind": "debuff",
             "stat": "atk", "mult": 0.8, "turns": 2, "w": 2},
            {"name": "Morso del Vuoto", "power": 125, "element": "cinetico", "kind": "attack", "w": 4},
        ]},
    "sentinella": {
        "name": "Sentinella dei Tessitori", "sprite": "enemy_sentinella",
        "hp": 300, "en": 60, "atk": 13, "dfs": 9, "spd": 12,
        "weak": ["cinetico"], "resist": ["termico"], "exp": 170, "boss": True,
        "moves": [
            {"name": "Filo Recisore", "power": 115, "element": "ionico", "kind": "attack", "w": 5},
            {"name": "Trama d'Assedio", "power": 85, "element": "ionico", "kind": "attack_all", "w": 3},
            {"name": "Nodo Stretto", "power": 140, "element": "cinetico", "kind": "attack", "w": 2},
        ]},
    "custode": {
        "name": "Il Custode", "sprite": "enemy_custode",
        "hp": 560, "en": 999, "atk": 15, "dfs": 10, "spd": 13,
        "weak": ["bio", "cinetico"], "resist": ["ionico"], "exp": 420, "boss": True,
        # pattern ciclico fisso (vedi battle.py): niente pesi
        "moves": [
            {"name": "Verdetto", "power": 130, "element": "ionico", "kind": "attack"},
            {"name": "Lamento Statico", "power": 80, "element": "ionico", "kind": "attack_all"},
            {"name": "Protocollo di Quiete", "power": 0, "element": "ionico", "kind": "debuff",
             "stat": "atk", "mult": 0.85, "turns": 2},
            {"name": "Abbraccio Gelido", "power": 145, "element": "cinetico", "kind": "attack"},
        ]},
}

# id battaglia -> composizione
BATTLES = {
    "b_tutorial":      {"enemies": ["drone_a", "drone_a"], "bg": "battle_ship",
                        "music": "battle", "flee": False,
                        "intro": "Due droni di manutenzione bloccano il corridoio!"},
    "b_anomalia_hab":  {"enemies": ["drone_a", "drone_b"], "bg": "battle_ship", "music": "battle"},
    "b_officina":      {"enemies": ["drone_a", "drone_b", "drone_a"], "bg": "battle_ship",
                        "music": "battle", "flee": False,
                        "intro": "I droni dell'officina vi puntano in massa!"},
    "b_anomalia_off":  {"enemies": ["drone_b", "drone_b"], "bg": "battle_ship", "music": "battle"},
    "b_spore1":        {"enemies": ["spora", "spora"], "bg": "battle_hydro", "music": "battle"},
    "b_spore2":        {"enemies": ["spora", "spora", "spora"], "bg": "battle_hydro",
                        "music": "battle", "flee": False,
                        "intro": "Le spore sciamano tra i filari!"},
    "b_anomalia_idro": {"enemies": ["spora", "ombra"], "bg": "battle_hydro", "music": "battle"},
    "b_rovine1":       {"enemies": ["ombra", "ombra"], "bg": "battle_ruins", "music": "battle"},
    "b_rovine2":       {"enemies": ["ombra", "spora", "ombra"], "bg": "battle_ruins", "music": "battle"},
    "b_anomalia_cuore": {"enemies": ["ombra", "ombra"], "bg": "battle_ruins", "music": "battle"},
    "b_sentinella":    {"enemies": ["sentinella"], "bg": "battle_ruins", "music": "boss",
                        "flee": False,
                        "intro": "La Sentinella si ricompone filo dopo filo: vi sta MISURANDO."},
    "b_custode":       {"enemies": ["custode"], "bg": "battle_ruins", "music": "boss",
                        "flee": False,
                        "intro": "«PROTOCOLLO DI QUIETE. Dormirete. Sarete al sicuro. Per sempre.»"},
}
