# Contratto asset — AURIGA (documento interno di build)

> Documento tecnico usato durante la produzione degli asset: definisce
> ESATTAMENTE i path e i formati che `asset_loader.py` si aspetta. Non serve
> per giocare; le fonti e le licenze degli asset sono in [ASSETS.md](ASSETS.md).

Chi produce gli asset deve rispettarlo alla lettera. Radice: `auriga/assets/`.

Regole generali:
- Solo PNG con trasparenza per la grafica; WAV oppure OGG per l'audio
  (il loader prova prima `.ogg` poi `.wav`).
- Licenze ammesse per materiale scaricato: CC0 o CC-BY (annotare autore e URL in ASSETS.md).
- Ogni immagine deve essere davvero leggibile (verificare con Pillow), non un HTML di errore.

## 1. `assets/tiles/` — un PNG per tile, 48x48 px finali

Se la sorgente è 16x16 o 32x32, upscalare con NEAREST (pixel-art nitida).
I tile "floor" devono essere completamente opachi; gli oggetti (crate, plant, ...) hanno
trasparenza e si disegnano SOPRA un floor.

Nave (interni sci-fi, palette coerente):
- floor_ship_a.png, floor_ship_b.png  (due varianti di pavimento)
- floor_hall.png                       (corridoio, visivamente diverso)
- wall_ship.png, wall_ship_top.png     (muro visto frontale + bordo superiore)
- door_closed.png, door_open.png
- console.png, console_glow.png        (stessa console, spenta/attiva)
- crate.png, barrel.png, bed.png, table.png, chair.png, locker.png
- plant_pot.png, pipe.png, vent.png
- window_star.png                      (finestra con stelle, opaco)
- hatch.png                            (botola/portello a pavimento)

Idroponica:
- floor_hydro.png (opaco, verdeggiante/tech), planter_a.png, planter_b.png, tree_glow.png

Rovine dei Tessitori (può essere il set nave ri-colorato in viola/ciano con Pillow):
- floor_ruin_a.png, floor_ruin_b.png (opachi), wall_ruin.png, wall_ruin_top.png
- glyph_floor.png, glyph_wall.png     (glifi luminosi)
- pillar.png, rubble.png, crystal_a.png, crystal_b.png, altar.png

Interattivi (con trasparenza):
- savepoint.png, chest_closed.png, chest_open.png, terminal_story.png, elevator.png
- anomaly.png                          (segnalino nemico su mappa: scintilla/drone)

## 2. `assets/characters/` — spritesheet camminata + meta.json

Layout UNIFORME per tutti gli sheet: griglia 3 colonne x 4 righe.
Righe dall'alto: down, left, right, up. Colonne: frame di camminata (il frame 1 è idle).
`meta.json`:
```json
{"layout": "3x4", "order": ["down", "left", "right", "up"],
 "sheets": {"kaira": {"fw": 16, "fh": 18}, "...": {"fw": 0, "fh": 0}}}
```
(fw/fh = dimensioni reali del singolo frame nel PNG; il gioco scala da sé a ~3x.)

Sheet richiesti (personaggi distinguibili tra loro; ok ri-tinte con Pillow):
- kaira.png   (donna, capelli rossi, tuta teal/arancio)
- ilan.png    (uomo, capelli scuri, abito da studioso)
- sette.png   (androide, placche bianche/blu — ok tinta metallica di uno sprite umano)
- naia.png    (donna, capelli verde-teal, tuta da botanica)
- npc_ada.png (medica, capelli grigi), npc_bruno.png (tecnico robusto), npc_luce.png (bambina)
- custode.png (avatar olografico: sprite ri-tinto blu/trasparente ok)

## 3. Sprite nemici (battaglia) — `assets/characters/`

PNG statici con trasparenza, lato maggiore >= 96 px (upscale NEAREST ok), stile coerente:
- enemy_drone_a.png, enemy_drone_b.png   (droni di manutenzione impazziti)
- enemy_spora.png                        (spora-ombra biotica)
- enemy_sentinella.png                   (sentinella dei Tessitori, elegante)
- enemy_ombra.png                        (frammento d'ombra del Custode)
- enemy_custode.png                      (boss: nucleo/occhio olografico, >= 160 px)

## 4. `assets/portraits/` — ritratti anime cel-shaded, PNG ~320x320+

Busto, sguardo verso lo spettatore, lineart pulito, colori piatti vivaci, SFW ed eleganti:
- kaira.png  — donna ~30 anni, capelli rossi corti mossi, jumpsuit da capitano teal/arancio, sorriso sbilenco deciso
- ilan.png   — uomo ~32, pelle olivastra, occhiali sottili, capelli scuri legati, cardigan su uniforme, aria gentile
- sette.png  — androide androgino elegante, placche bianche e blu, occhi ambra luminosi
- naia.png   — donna ~26, pelle scura, lentiggini, capelli verde-teal raccolti, tuta con fiori bioluminescenti, sorriso solare
- ada.png    — medica ~50, capelli grigi raccolti, sguardo materno
- bruno.png  — tecnico robusto, barba, bandana
- luce.png   — bambina ~10, treccine, curiosa (stile bambino del tutto innocente)
- custode.png — volto olografico geometrico blu freddo, austero

## 5. `assets/backgrounds/` — PNG

- title.png   1280x720 (scena spaziale anime: nave-arca alla deriva, nebulosa — può essere SD-Turbo upscalato)
- ending.png  1280x720 (alba stellare, tono di speranza)
- battle_ship.png, battle_hydro.png, battle_ruins.png  1280x720 (sfondi battaglia; ok composizioni dai tile sfocate/scurite)
- space.png   tile di stelle affiancabile (>= 256x256, seamless)

## 6. `assets/ui/` e `assets/fonts/`

UI (PNG, stile sci-fi pulito):
- panel.png        (pannello 9-slice, >= 96x96, bordi a 16 px)
- button.png, button_sel.png  (>= 190x45)
- cursor.png       (freccia/indicatore, ~24-32 px)
- slot.png         (casella inventario ~48x48)
- bar_bg.png, bar_hp.png, bar_en.png, bar_xp.png  (barre orizzontali stirabili, ~8-12 px di altezza)
- icon_kinetic.png, icon_thermal.png, icon_ion.png, icon_bio.png (icone elemento 16-32 px)

Font (TTF/OTF, licenza OFL — es. da github.com/google/fonts):
- fonts/title.ttf   (display futuristico, es. Exo 2 / Orbitron)
- fonts/text.ttf    (leggibile, es. Rajdhani Regular)
- fonts/text_bold.ttf

## 7. `assets/music/` — tracce originali sintetizzate (numpy), mood alla Honkai: Star Rail

WAV 16-bit stereo (22050 o 44100 Hz) oppure OGG. Loop-friendly (niente click al riavvio).
- title.wav    ~60-90 s — piano emotivo + pad caldo, meraviglia (es. Am–F–C–G lento)
- explore.wav  ~60-90 s — calmo, curioso, arpeggi delicati
- hydro.wav    ~60-90 s — verde, sognante, campanelli morbidi
- ruins.wav    ~60-90 s — misterioso, corale sintetico, riverbero
- battle.wav   ~60-90 s — energico 120-132 BPM, percussioni leggere, riff sintetico
- boss.wav     ~60-90 s — teso, epico, basso insistente
- victory.wav  ~6-10 s  — jingle luminoso (non loop)
- ending.wav   ~60-90 s — commosso, risolutivo, tema del titolo ripreso in maggiore

## 8. `assets/sfx/` — effetti brevi (WAV/OGG, < 2 s salvo victory)

confirm, cancel, move, hit, crit, heal, buff, skill, door, save, item, flee, glyph,
levelup, encounter, gameover  → es. `confirm.wav` …
(da Kenney "Interface Sounds" / "Sci-Fi Sounds", CC0; rinominare copie sui nomi sopra)

## Fallback

Se un file manca, `asset_loader.py` genera un segnaposto colorato: il gioco non deve
MAI crashare per un asset mancante. Ma l'obiettivo è che il fallback non serva mai.
