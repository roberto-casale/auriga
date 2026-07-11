"""Oggetti: consumabili e oggetti chiave."""

# kind: heal | heal_all | en | revive | key
ITEMS = {
    "razione": {
        "name": "Razione Rinforzata", "kind": "heal", "amount": 60,
        "desc": "Cibo dell'Auriga, insospettabilmente buono. +60 HP."},
    "gel": {
        "name": "Gel Medicale", "kind": "heal", "amount": 150,
        "desc": "Gel rigenerante di derivazione idroponica. +150 HP."},
    "cella": {
        "name": "Cella d'Energia", "kind": "en", "amount": 40,
        "desc": "Ricarica compatta. +40 EN."},
    "stimolante": {
        "name": "Stimolante", "kind": "revive", "amount": 0.5,
        "desc": "Rimette in piedi un alleato KO con metà HP."},
    "fiala_luce": {
        "name": "Fiala di Luce", "kind": "heal_all", "amount": 80,
        "desc": "Linfa dell'albero-lume: +80 HP a tutto il party."},

    # ------------------------------------------------------ oggetti chiave
    "chiave_magnetica": {
        "name": "Chiave Magnetica", "kind": "key",
        "desc": "Apre l'ascensore di servizio per l'Anello Idroponico."},
    "sigillo_tessitori": {
        "name": "Sigillo dei Tessitori", "kind": "key",
        "desc": "Un disco di metallo caldo, percorso da fili di luce."},
    "diario_capitano": {
        "name": "Diario del Capitano Rhee", "kind": "key",
        "desc": "Le ultime pagine parlano di 'una voce sotto il pavimento'."},
}
