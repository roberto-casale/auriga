# Provenienza degli asset di AURIGA

Tutti gli asset del gioco sono file reali in `assets/`, o scaricati da fonti
libere (CC0 / CC-BY) o generati in locale su questa macchina. Nessun asset è
disegnato a codice a runtime (i segnaposto colorati esistono solo come rete di
sicurezza in `asset_loader.py`).

## Grafica scaricata

| Categoria | Pack / File | Autore | Licenza | URL |
|---|---|---|---|---|
| Tile interni nave/rovine (`assets/tiles/`) | Sci-fi Interior Tiles | Buch | CC0 | https://opengameart.org/content/sci-fi-interior-tiles |
| Tile aggiuntivi (pavimenti, idroponica) | Colony Sim Assets | Buch | CC0 | https://opengameart.org/content/colony-sim-assets |
| Tile aggiuntivi (varianti) | Colony Sim Extended | rubberduck (da Buch) | CC0 | https://opengameart.org/content/colony-sim-extended-version |
| Spritesheet camminata (`assets/characters/*.png`) | Twelve 16x18 RPG sprites, plus base | Antifarea (commissionato da OpenGameArt.org, account charlesgabriel) | **CC-BY 3.0** | https://opengameart.org/content/twelve-16x18-rpg-sprites-plus-base |
| Sprite nemici (droni, ombre, boss) | Space Shooter Redux | Kenney Vleugels (kenney.nl) | CC0 | https://opengameart.org/content/space-shooter-redux (mirror ufficiale; kenney.nl dava errore) |
| UI: pannelli, bottoni, barre, cursore (`assets/ui/`) | UI Pack – Space Expansion | Kenney | CC0 | https://kenney.nl/assets/ui-pack-sci-fi |
| Icone elemento | Game Icons + Board Game Icons | Kenney | CC0 | https://kenney.nl/assets/game-icons · https://kenney.nl/assets/board-game-icons |

Le ri-tinte (capelli di Kaira rossi, Sette metallico, Custode olografico,
droni/ombre/boss ricolorati e ricomposti) sono state fatte con Pillow a partire
dai PNG originali; i layout degli spritesheet sono stati riassemblati nel
formato 3x4 descritto in `ASSET_CONTRACT.md`.

**Attribuzione richiesta (CC-BY):** gli sprite di camminata sono di
*Antifarea, commissionati da OpenGameArt.org*.

## Font (`assets/fonts/`)

| File | Font | Autore | Licenza |
|---|---|---|---|
| `title.ttf` | Exo 2 (variabile) | Natanael Gama (NDISCOVER) | SIL OFL 1.1 |
| `text.ttf` / `text_bold.ttf` | Rajdhani Regular / Bold | Indian Type Foundry | SIL OFL 1.1 |

Scaricati da https://github.com/google/fonts (cartella `ofl/`).

## Audio

- **Effetti (`assets/sfx/*.ogg`)** — copie rinominate dai pack CC0 di Kenney:
  *Interface Sounds*, *Sci-Fi Sounds*, *Digital Audio*, *Impact Sounds*
  (https://kenney.nl/assets/…). Nessuna modifica ai file.
- **Musica (`assets/music/*.ogg`)** — **8 tracce originali** composte nota per
  nota e sintetizzate in numpy da `tools/gen_music.py` (piano additivo, pad,
  campanelli FM, percussioni sintetiche, riverbero Schroeder). Nessun sample
  esterno: sono di questo progetto. Prodotte in WAV e poi convertite in OGG
  Vorbis (via `soundfile`) per il web: 41 MB → ~3 MB senza perdita percepibile.

## Ritratti e scenari (`assets/portraits/`, `title.png`, `ending.png`)

Generati **in locale** con SD-Turbo (`stabilityai/sd-turbo`, licenza Stability AI
Community) tramite `tools/generate_portraits_sd.py`, su CPU, in stile anime
cel-shaded; selezione manuale tra più seed. Sono output originali prodotti su
questa macchina; nessuna immagine è stata scaricata.

## Ritocchi finali

`floor_ship_b`, `wall_ship_top` e `floor_hall` sono stati attenuati con Pillow
(contrasto/saturazione) per la leggibilità della mappa.
