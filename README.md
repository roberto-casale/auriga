# AURIGA — Il Richiamo dei Tessitori

RPG sci-fi 2D a turni in **puro Python + pygame**, con estetica anime
cel-shaded. La nave-arca *Auriga* è alla deriva da trecento anni quando strani
glifi luminosi — i fili di un'antica civiltà, i **Tessitori** — cominciano ad
apparire sulle paratie. Kaira, Ilan, Sette e Naia li seguiranno fino al Cuore
della nave.

- **Finestra:** 1280x720, 60 FPS, solo sprite 2D — pensato per girare fluido
  su un MacBook Pro 2015 con grafica integrata.
- **Lingua:** italiano. **Durata:** ~40–60 minuti. **Difficoltà:** facile
  (checkpoint generosi, si può salvare ovunque dal menu).

## Avvio (desktop)

Il gioco usa il venv della cartella padre `test_py/.venv` (pygame 2.6.1 già
installato — vedi `requirements.txt`).

```bash
cd auriga
../.venv/bin/python main.py
```

In alternativa, dalla cartella `test_py`:

```bash
.venv/bin/python auriga/main.py
```

## Giocare nel browser (WebAssembly)

Il gioco gira anche in un browser, senza installare niente, grazie a
[pygbag](https://pygame-web.github.io/) (compila in WebAssembly). Il ciclo di
gioco in `main.py` è `async` proprio per questo.

**Anteprima locale:**

```bash
cd auriga
../.venv/bin/pip install pygbag        # una volta
../.venv/bin/pygbag main.py            # compila e serve su http://localhost:8000
```

Apri **http://localhost:8000** nel browser (il primo avvio scarica il runtime;
attendi ~30-60 s). Se il download del runtime dà errore SSL, anteponi
`SSL_CERT_FILE=$(../.venv/bin/python -c 'import certifi; print(certifi.where())')`.

**Solo build (cartella statica da pubblicare):**

```bash
../.venv/bin/pygbag --build main.py    # produce build/web/
```

### Pubblicare su GitHub Pages

Il repository include una GitHub Action ([.github/workflows/deploy.yml](.github/workflows/deploy.yml))
che compila e pubblica il gioco a ogni push. Una volta sola:

1. Crea un repository su GitHub e collega questa cartella:
   ```bash
   cd auriga
   git remote add origin https://github.com/<tuo-utente>/auriga.git
   git push -u origin main
   ```
2. Su GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Attendi che l'Action "Deploy AURIGA su GitHub Pages" finisca (tab **Actions**).
4. Il gioco sarà su **https://<tuo-utente>.github.io/auriga/** — condividi il link!

Da lì in poi ogni `git push` ricompila e aggiorna il gioco online da solo.

> Nota: nel browser i salvataggi valgono per la sessione (il gioco usa comunque
> i 3 slot). Su desktop restano su file in `saves/`.

### Da smartphone / tablet

Il sito è una **PWA**: aprendo il link dal telefono si può fare *Aggiungi alla
schermata Home* (Android: menu ⋮ → Installa app; iPhone: Condividi → Aggiungi
alla schermata Home) e il gioco parte a schermo intero con l'icona di Kaira.

Sui dispositivi touch compaiono automaticamente i **tasti a schermo**
(`core/touch.py`, attivi solo lì — su desktop non appaiono):
- **croce direzionale** (sinistra): movimento e navigazione nei menu;
- **A** (destra): conferma / interagisci / avanza dialogo;
- **B**: menu di pausa / annulla.

Consigliato l'orientamento orizzontale. Il livello PWA (manifest, icone,
service worker senza cache) è in `web_extra/` e viene applicato al deploy da
`tools/pwa_patch.py`.

## Comandi

| Tasto | Azione |
|---|---|
| Frecce / WASD | Movimento |
| SPAZIO / INVIO | Interagisci · Conferma · Avanza dialogo |
| ESC | Menu di pausa (Stato, Zaino, Salva, Opzioni) · Annulla |
| X / BACKSPACE | Annulla nei menu |
| F12 | Screenshot (`screenshot.png`) |

## Gameplay

- **Combattimento a turni** con party fino a 4: Attacca, Abilità (costano EN),
  Oggetti, Difendi, Fuggi. Quattro elementi (Cinetico, Termico, Ionico, Bio)
  con debolezze ×1.5 e resistenze ×0.5 — le debolezze dei nemici sono sempre
  visibili sotto la loro barra HP.
- **Esplorazione a tile** su 4 zone della nave, dialoghi con scelte (alcune
  fanno crescere le *affinità* tra i personaggi e cambiano l'epilogo), bauli,
  anomalie da bonificare, punti di salvataggio che curano il party.
- **Salvataggio** su 3 slot (file JSON in `saves/`), dal menu di pausa o ai
  punti di salvataggio; caricamento dal titolo.
- **Sconfitta gentile:** se il party cade, si riparte dall'ultimo checkpoint
  con metà HP. Nessun progresso perso.

## Suggerimenti senza spoiler

- Parlate con tutti (Ada vi cura gratis) ed esaminate gli oggetti curiosi:
  qualche sorriso è nascosto qua e là.
- La scena alla vetrata dell'idroponica e quella all'Albero-Lume sono opzionali
  ma… consigliate a chi ha cuore.
- Nel Cuore servono tre glifi prima dell'altare.

## Struttura del codice

```
main.py            avvio e ciclo di gioco
settings.py        costanti (finestra, colori, elementi, tasti)
asset_loader.py    caricamento centralizzato di assets/ (fallback inclusi)
core/              scene manager, audio, testo, widget UI
game/              statistiche, abilità, oggetti, nemici, party, salvataggi, storia
world/             tilemap, dati delle 4 mappe, entità
scenes/            titolo, esplorazione, dialoghi, battaglia, menu, finale
tools/             validatore, smoke test, playthrough automatico,
                   generatore musica (numpy), generatore ritratti (SD-Turbo)
assets/            grafica/audio reali — provenienza e licenze in ASSETS.md
```

## Test

```bash
../.venv/bin/python tools/validate.py      # coerenza di mappe/eventi/riferimenti
../.venv/bin/python tools/smoke_boot.py    # avvio headless rapido
../.venv/bin/python tools/playthrough.py   # gioca TUTTA la partita da solo (31 traguardi)
```

Il playthrough automatico percorre l'intera storia (dialoghi, scelte, battaglie,
boss, salvataggio/caricamento, sconfitta e respawn) in headless e fallisce se
un passaggio si rompe.

## Crediti asset

Tile e sprite da pack CC0/CC-BY (Kenney, Buch, Antifarea — sprite camminata di
Antifarea commissionati da OpenGameArt.org, CC-BY 3.0), ritratti generati in
locale con SD-Turbo, musica originale sintetizzata in numpy. Dettagli completi
in [ASSETS.md](ASSETS.md). Progetto per testing personale, non per
distribuzione.
