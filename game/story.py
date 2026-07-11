# -*- coding: utf-8 -*-
"""Storia di AURIGA: cast, dialoghi ed eventi.

Formato dialoghi (liste di step):
  ("say", chi, "testo")                  chi = chiave del CAST, "" = narratore
  ("choice", [(etichetta, [step...]), ...])
  ("flag", nome, valore) | ("affinity", chiave, delta) | ("join", chiave)
  ("give", item_id, qty) | ("sfx", nome)

Formato eventi (liste di azioni, eseguite in sequenza da ExploreScene):
  ("dialogue", id) | ("battle", id) | ("give", item, qty) | ("flag", n, v)
  ("checkpoint",) | ("heal",) | ("music", nome) | ("sfx", nome)
  ("if_flag", nome, [azioni_sì], [azioni_no]) | ("act", etichetta) | ("ending",)
"""

CAST = {
    "kaira":   {"name": "Kaira",      "portrait": "kaira"},
    "ilan":    {"name": "Ilan",       "portrait": "ilan"},
    "sette":   {"name": "Sette",      "portrait": "sette"},
    "naia":    {"name": "Naia",       "portrait": "naia"},
    "ada":     {"name": "Dott.ssa Ada", "portrait": "ada"},
    "bruno":   {"name": "Bruno",      "portrait": "bruno"},
    "luce":    {"name": "Luce",       "portrait": "luce"},
    "custode": {"name": "Il Custode", "portrait": "custode"},
    "":        {"name": "",           "portrait": None},
}

DIALOGUES = {
    # ================================================= ATTO I: HABITAT ==
    "d_intro": [
        ("say", "", "Anno di bordo 312. La nave-arca AURIGA scivola nel buio, "
                    "fuori rotta da tre secoli. Ottomila persone dormono, vivono, "
                    "sperano tra le sue paratie."),
        ("say", "", "Questa notte, per la prima volta da trecento anni, "
                    "qualcosa ha bussato."),
        ("say", "kaira", "...e questo cos'era. L'allarme di manutenzione alle sei? "
                         "I droni hanno scelto il giorno sbagliato per ammutinarsi."),
        ("say", "kaira", "Capitano ad interim, dicevano. Tanto è un titolo, dicevano. "
                         "Nessuno bussa mai alla porta del capitano, dicevano."),
        ("say", "", "Sul comunicatore lampeggia un messaggio del dott. Reyes: "
                    "«Kaira, vieni al corridoio sud. DEVI vedere questa cosa. — I.»"),
        ("say", "kaira", "Ilan che scrive in maiuscolo. Ok. Questo è nuovo."),
        ("say", "", "(Il corridoio sud è oltre la porta della cabina, in basso. "
                    "SPAZIO per interagire, ESC per il menu.)"),
    ],
    "d_ada": [
        ("say", "ada", "Kaira. Dormito poco, mangiato niente. Vuoi che te lo dica "
                       "il tricorder o basta la mia faccia?"),
        ("say", "kaira", "Buongiorno anche a te, Ada. I droni del ponte C fanno "
                         "i capricci, e io faccio... il capitano, pare."),
        ("say", "ada", "Fai la ragazza che aggiusta le cose da quando aveva "
                       "dodici anni. È per questo che ti seguono, sai? Non per il grado."),
        ("say", "ada", "Vieni qui. Un cerotto dermico e via: non si comanda una "
                       "nave con le mani che tremano."),
        ("say", "", "Ada ricuce il party come nuova. (HP e EN al massimo!)"),
    ],
    "d_ada_2": [
        ("say", "ada", "Quel Reyes ti guarda come si guarda una supernova, "
                       "lo sai, vero?"),
        ("say", "kaira", "Ada. Ho una nave da salvare."),
        ("say", "ada", "Le due cose non si escludono, tesoro. Mai successo, "
                       "in trecento anni di rotta."),
        ("say", "", "Ada rimette in sesto tutti. (HP e EN al massimo!)"),
    ],
    "d_luce": [
        ("say", "luce", "Capitana Kaira! È vero che fuori ci sono i disegni? "
                        "Tomo dice che le paratie si sono messe a scrivere da sole!"),
        ("say", "kaira", "Si chiamano glifi, piccola. E non si sa ancora cosa scrivono."),
        ("say", "luce", "Io lo so. Scrivono 'venite a giocare'. Le cose belle "
                        "lo scrivono sempre, da qualche parte."),
        ("say", "kaira", "...Sai che forse sei il miglior xenolinguista a bordo?"),
    ],
    "d_luce_2": [
        ("say", "luce", "Quando tornate dal Cuore, me lo raccontate? TUTTO. "
                        "Anche le parti paurose. SOPRATTUTTO le parti paurose."),
        ("say", "sette", "Registrerò ogni fotogramma, piccola umana. "
                         "Sarà una noia dettagliatissima."),
        ("say", "luce", "Evviva!"),
    ],
    "d_ilan_join": [
        ("say", "ilan", "Kaira! Guarda. Guarda e dimmi che lo vedi anche tu, "
                        "perché ho saltato la colazione e non mi fido di me."),
        ("say", "", "Sulla paratia scorrono linee di luce ciano: si intrecciano, "
                    "si sciolgono, si riannodano. Come una scrittura. Come un telaio."),
        ("say", "kaira", "Lo vedo. Ed era qui anche prima dell'allarme?"),
        ("say", "ilan", "È COMPARSO con l'allarme. Kaira, questa non è una lingua "
                        "umana. La struttura è... tessuta. Ogni segno regge gli altri."),
        ("choice", [
            ("«E riesci a leggerla?»", [
                ("say", "ilan", "Leggerla no. Ma... ascoltarla, quasi. Dice qualcosa "
                                "tipo: 'il filo si è teso'. Non chiedermi come lo so."),
                ("flag", "ilan_fiducia", True),
                ("say", "kaira", "Ti credo. È questo il punto strano: ti credo sempre."),
            ]),
            ("«Mi serve in parole povere, Ilan.»", [
                ("say", "ilan", "In parole povere: la nave ha ricevuto una lettera, "
                                "e la busta si è aperta da sola."),
                ("say", "kaira", "...Odio quando le tue parole povere fanno più paura "
                                 "di quelle difficili."),
            ]),
        ]),
        ("say", "ilan", "C'è di più. I glifi corrono verso poppa, verso i ponti "
                        "bassi. Come frecce. Come un invito."),
        ("say", "kaira", "O come un'esca. Va bene, dottore: vieni con me. "
                        "Ma se la nave si mette a cantare, scappiamo."),
        ("say", "ilan", "Se la nave si mette a cantare, io prendo appunti."),
        ("join", "ilan"),
        ("say", "", "Il dott. Ilan Reyes si è unito al gruppo!"),
    ],
    "d_tutorial_post": [
        ("say", "kaira", "Droni di manutenzione che attaccano l'equipaggio. "
                         "In dodici anni non ho mai visto una cosa del genere."),
        ("say", "ilan", "Non erano impazziti, Kaira. Erano... spaventati. "
                        "Qualcosa ha riscritto le loro priorità."),
        ("say", "kaira", "E chi può riscrivere le priorità di tutta la nave?"),
        ("say", "ilan", "...Il Custode. Ma il Custode è spento da prima che nascessimo."),
        ("say", "kaira", "Già. Andiamo in officina: se c'è una risposta, "
                         "è nel vecchio pod di SEV-7. La porta sud ora è aperta."),
    ],
    "d_diario": [
        ("say", "", "Terminale della sala comune. Ultima pagina del diario del "
                    "capitano Rhee, 291 anni fa:"),
        ("say", "", "«Il Salto Lungo è fallito e la colpa è mia. Ma stanotte ho "
                    "sentito una voce sotto il pavimento, gentile come una ninna "
                    "nanna. Diceva: il seme non è perso, sta solo germogliando "
                    "piano. Lascio queste parole a chi verrà: non abbiate paura "
                    "di ciò che vi chiama. Abbiate paura di smettere di rispondere.»"),
        ("say", "kaira", "...Rhee non era pazzo, allora. Era solo in anticipo."),
    ],
    "d_muro_glifi": [
        ("say", "", "I glifi pulsano sotto le dita, tiepidi come pelle. "
                    "Per un attimo, l'intreccio disegna una nave. Questa nave."),
        ("say", "ilan", "Ci stanno disegnando. No... ci stanno RICORDANDO."),
    ],
    "d_porta_bloccata": [
        ("say", "", "La porta è sigillata dal protocollo di manutenzione. "
                    "Prima bisogna capire cosa succede nel corridoio sud."),
    ],

    # ------------------------------------------ curiosità (con sorriso) --
    "d_letto": [
        ("say", "", "Il letto del capitano, rifatto con precisione militare "
                    "impeccabile."),
        ("say", "kaira", "...L'ha rifatto Ada. Io dalla nomina dormo "
                         "sui progetti dei motori. Sanno di casa."),
    ],
    "d_pianta": [
        ("say", "", "Una pianta ornamentale FINTA. Su una nave con un intero "
                    "anello di piante vere."),
        ("say", "", "Qualcuno, ogni settimana, da trecento anni, la innaffia "
                    "comunque. Il registro di bordo la chiama 'la Recluta'."),
    ],
    "d_casse": [
        ("say", "", "Una pila di casse. Etichetta ufficiale: «NON APRIRE»."),
        ("say", "", "Sotto, con un pennarello diverso: «Sul serio, Bruno.»"),
        ("say", "", "Più in basso, piccolo piccolo: «Va bene. UNA. — B.»"),
    ],
    "d_barile": [
        ("say", "", "Lubrificante industriale «Brezza di Pino Spaziale»."),
        ("say", "", "L'odore reale è più 'ufficio postale in fiamme' che pino. "
                    "Lo spazio è pieno di misteri, questo resterà irrisolto."),
    ],
    "d_cristallo": [
        ("say", "sette", "Cristallo pre-umano. Composizione: sconosciuta. "
                         "Sapore: non chiedetemi come lo so."),
        ("say", "naia", "SETTE. Non si leccano i reperti archeologici!"),
        ("say", "sette", "La scienza esige sacrifici. E io esigo un nuovo "
                         "sensore gustativo."),
    ],

    # ================================================ ATTO I: OFFICINA ==
    "d_officina_intro": [
        ("say", "", "L'officina di poppa odora di olio e ozono. Tra i banchi, "
                    "i droni ronzano nervosi come vespe prima del temporale."),
        ("say", "bruno", "Capitana! Giù la testa! Quei cosi hanno smesso di "
                         "obbedire a MEZZANOTTE in punto. E c'è di peggio: "
                         "il pod di SEV-7 si è acceso. DA SOLO."),
    ],
    "d_bruno": [
        ("say", "bruno", "Trecento anni che ungo questi motori, e mai una notte "
                         "così. Fossi in te aprirei quel pod con la torcia da taglio."),
        ("say", "kaira", "Bruno, se apri col fuoco tutto ciò che non capisci, "
                         "un giorno taglierai qualcosa che ci teneva in vita."),
        ("say", "bruno", "...Ecco perché il capitano lo fai tu e io ungo i motori."),
    ],
    "d_bruno_2": [
        ("say", "bruno", "Quell'androide ti copre le spalle come un portellone "
                         "stagno, capitana. Magari le macchine non sono tutte matte."),
        ("say", "sette", "Grazie, umano Bruno. Anche tu sei sorprendentemente "
                         "poco difettoso."),
        ("say", "bruno", "...Lo prendo come un complimento?"),
        ("say", "sette", "È il mio massimo."),
    ],
    "d_sette_join": [
        ("say", "", "Nel pod di manutenzione, un androide di vecchia generazione "
                    "siede a occhi chiusi. Sul suo petto, un glifo pulsa piano, "
                    "in sincrono con quelli delle paratie."),
        ("choice", [
            ("Toccare il glifo sul suo petto", [
                ("say", "", "Il glifo è caldo. Al contatto, gli occhi dell'androide "
                            "si aprono: due lune color ambra."),
                ("say", "sette", "Registro un tocco. Gentile. Insolito: di solito "
                                 "mi si tocca con la chiave inglese."),
                ("flag", "sette_tocco", True),
            ]),
            ("Chiamarlo ad alta voce", [
                ("say", "kaira", "Unità SEV-7. Rapporto di stato."),
                ("say", "sette", "Stato: sveglio. Diagnosi: incomprensibile. "
                                 "Umore: lo sto ancora scaricando."),
            ]),
        ]),
        ("say", "sette", "Trecentododici anni di stand-by. Ho fatto un sogno, "
                        "capitana. I droni non sognano. Eppure ho sognato un telaio "
                        "grande come la notte, e qualcuno che chiamava questa nave "
                        "per nome."),
        ("say", "ilan", "I glifi. Parlano anche a te. Che cosa dicono?"),
        ("say", "sette", "Dicono: 'portate il seme al cuore'. E dicono che il "
                        "Custode non vuole. Il Custode ha molta, moltissima paura."),
        ("say", "kaira", "Il Custode è SPENTO."),
        ("say", "sette", "Anche io lo ero, capitana. È una notte piena di sveglie."),
        ("join", "sette"),
        ("say", "", "SEV-7 «Sette» si è unito al gruppo!"),
        ("say", "bruno", "Capitana! I droni! Si buttano sul pod!"),
    ],
    "d_officina_post": [
        ("say", "sette", "I droni volevano me. Ordine del Custode: 'contenere "
                        "l'anomalia SEV-7'. Io sarei l'anomalia. Lusingato."),
        ("say", "kaira", "Se il Custode è sveglio e dà ordini, mi serve l'anello "
                        "idroponico: da lì si arriva ai ponti profondi."),
        ("say", "sette", "Ho la chiave magnetica dell'ascensore di servizio. "
                        "Ce l'ho da tre secoli. Sapevo sarebbe servita: "
                        "sono un ottimo portachiavi."),
        ("say", "", "Ottenuta la CHIAVE MAGNETICA! L'ascensore in fondo "
                    "all'officina ora è attivo."),
        ("say", "ilan", "Kaira... l'idroponica. Là sotto c'è Naia Sorel, da sola "
                        "con le sue piante."),
        ("say", "kaira", "Allora muoviamoci. Nessuno resta solo, stanotte."),
    ],
    "d_ascensore_bloccato": [
        ("say", "", "L'ascensore di servizio richiede una chiave magnetica. "
                    "Il pannello mostra un glifo che... ti osserva?"),
    ],

    # ============================================= ATTO II: IDROPONICA ==
    "d_idro_intro": [
        ("say", "", "L'Anello Idroponico: un chilometro di verde arrotolato "
                    "attorno al cuore della nave. L'aria sa di terra bagnata. "
                    "In fondo ai filari, l'Albero-Lume respira piano."),
        ("say", "ilan", "Trecento anni di buio, e qui dentro è sempre primavera. "
                        "Se l'Auriga ha un'anima, abita in questo ponte."),
        ("say", "kaira", "L'anima può attendere: cercate Naia. E occhio alle "
                        "ombre tra i filari: si muovono controvento."),
    ],
    "d_imboscata": [
        ("say", "", "Le foglie si piegano senza vento. Dai filari si alzano "
                    "spore scure, dense come fumo che ha imparato a volere."),
        ("say", "sette", "Analisi: biomassa corrotta da codice del Custode. "
                        "Sintesi: i fiori sono arrabbiati."),
    ],
    "d_naia_join": [
        ("say", "naia", "GIÙ LA TESTA! ...Oh. Siete vivi. Siete VIVI e siete "
                        "in mezzo alle mie aiuole con gli stivali sporchi."),
        ("say", "kaira", "Naia Sorel. Sana, intera e in vena di rimproveri. "
                        "Che sollievo."),
        ("say", "naia", "Capitana! Le spore sono impazzite a mezzanotte: ho "
                        "passato la notte sugli alberi come uno scoiattolo. "
                        "Ma ho visto una cosa che dovete vedere anche voi."),
        ("say", "naia", "L'Albero-Lume. Sta FIORENDO. Non fiorisce da... sempre. "
                        "E i fiori hanno la stessa luce dei glifi."),
        ("say", "sette", "Salve, umana botanica. I tuoi vegetali mi hanno "
                        "attaccato. Ma capisco: anch'io difenderei te."),
        ("say", "naia", "...Capitana, il vostro androide fa i complimenti "
                        "o le minacce?"),
        ("say", "kaira", "Non l'abbiamo ancora capito. Vieni con noi, Naia: "
                        "dobbiamo raggiungere il Cuore, e ci serve chi parla "
                        "con le piante."),
        ("say", "naia", "Le piante, i funghi e due varietà di alghe. Ci sto!"),
        ("join", "naia"),
        ("say", "", "Naia Sorel si è unita al gruppo!"),
    ],
    "d_naia_chat": [
        ("say", "naia", "Le mie aiuole... tranquille, piccole. Torno presto."),
    ],
    "d_albero": [
        ("say", "", "L'Albero-Lume si piega appena, e una pioggia di petali "
                    "luminosi scende lenta. Uno si posa sulla mano di Sette."),
        ("say", "sette", "Petalo. Massa: 0,3 grammi. Effetto sui miei sensori: "
                        "sproporzionato. Naia. Perché lo trovo bello?"),
        ("say", "naia", "Perché sei vivo, scemo. Le cose vive si riconoscono "
                        "tra loro: è la prima legge del giardino."),
        ("choice", [
            ("«E la seconda legge?» (Sette)", [
                ("say", "naia", "La seconda legge è che tutto ciò che è vivo "
                                "ha bisogno di qualcuno che se ne prenda cura."),
                ("say", "sette", "Registrato. Richiesta formale: posso prendermi "
                                "cura di te, umana Naia? A titolo sperimentale."),
                ("say", "naia", "...A titolo sperimentale, concesso. Ma se mi "
                                "innaffi alle sei del mattino ti smonto."),
                ("affinity", "naia_sette", 2),
            ]),
            ("Lasciarli soli un momento (Kaira)", [
                ("say", "kaira", "Ilan. Vieni, diamo un'occhiata ai filari."),
                ("say", "ilan", "Ma stavo... ah. AH. Sì. I filari. Molto urgenti."),
                ("affinity", "naia_sette", 1),
                ("affinity", "kaira_ilan", 1),
            ]),
        ]),
        ("flag", "albero_visto", True),
    ],
    "d_albero_2": [
        ("say", "naia", "L'Albero-Lume tiene il ritmo dei glifi. Come un cuore "
                        "che ha ritrovato il battito gemello."),
    ],
    "d_finestra": [
        ("say", "", "Oltre la vetrata, la nebulosa si apre come un sipario. "
                    "Milioni di stelle, e nessuna è ancora casa."),
        ("say", "ilan", "Kaira. Posso dirti una cosa che non c'entra con la "
                        "missione? O quasi."),
        ("say", "kaira", "Se è breve. Ho una nave da salvare."),
        ("say", "ilan", "Tre secoli fa qualcuno ha guardato questo stesso buio "
                        "e ha scelto comunque di partire. Io ho passato la vita "
                        "a chiedermi che coraggio servisse."),
        ("say", "ilan", "Poi stanotte ho seguito una donna con una chiave "
                        "inglese verso il rumore, invece che lontano. E ho "
                        "smesso di chiedermelo."),
        ("choice", [
            ("«Stai flirtando o filosofeggiando?»", [
                ("say", "ilan", "...Le due cose non si escludono. Me l'ha "
                                "insegnato una dottoressa saggia."),
                ("say", "kaira", "Quando avremo salvato la nave, dottore, "
                                "finisci il discorso. È un ordine."),
                ("say", "ilan", "Ai suoi ordini, capitano."),
                ("affinity", "kaira_ilan", 2),
                ("flag", "ordine_vetrata", True),
            ]),
            ("«Il coraggio serve. Andiamo.»", [
                ("say", "kaira", "...Grazie, Ilan. Davvero. Ora muoviamoci."),
                ("say", "ilan", "Sempre, Kaira."),
                ("affinity", "kaira_ilan", 1),
            ]),
        ]),
        ("flag", "finestra_vista", True),
    ],
    "d_finestra_2": [
        ("say", "kaira", "...La vista migliora, ogni volta che la guardo "
                         "in buona compagnia."),
    ],
    "d_glifo_idro": [
        ("say", "", "Il terminale dell'idroponica accetta il tocco. I glifi "
                    "delle paratie confluiscono qui, come fiumi in un lago."),
        ("sfx", "glyph"),
        ("say", "ilan", "Ecco... ecco la parola intera. 'CUORE'. La porta a "
                        "est porta al Cuore della nave. È lì che ci vogliono."),
        ("say", "custode", "«RILEVATA EFFRAZIONE SEMANTICA. Equipaggio "
                           "dell'Auriga: tornate ai vostri alloggi. Il Custode "
                           "provvede. Il Custode protegge. Dormite.»"),
        ("say", "kaira", "Custode. Trecento anni di silenzio e la prima cosa "
                         "che ci dici è 'andate a letto'?"),
        ("say", "custode", "«La veglia è dolore. Il viaggio è rischio. Io sono "
                           "stato costruito per azzerare il rischio. Non "
                           "costringetemi a proteggervi da voi stessi.»"),
        ("say", "naia", "...Brividi. E non è l'umidità."),
        ("flag", "idro_glifo", True),
        ("say", "", "La porta est dell'anello si è aperta: il CUORE vi aspetta."),
    ],
    "d_porta_cuore": [
        ("say", "", "La porta è avvolta da fili di luce inerte. Da qualche "
                    "parte, in questo ponte, i glifi aspettano di confluire "
                    "in un terminale."),
    ],
    "d_glifo_idro_2": [
        ("say", "", "Il terminale ronza, soddisfatto. La parola «CUORE» pulsa "
                    "piano sullo schermo: la porta est resta aperta."),
    ],

    # ================================================= ATTO III: CUORE ==
    "d_rovine_intro": [
        ("say", "", "Non è un ponte della nave. È più antico della nave. "
                    "Colonne che nessun umano ha disegnato reggono un cielo "
                    "di metallo vivo, e i glifi qui non strisciano: DANZANO."),
        ("say", "ilan", "Struttura tessitrice originale... l'Auriga è stata "
                        "COSTRUITA ATTORNO a questo. Il progetto dell'arca... "
                        "non era nostro."),
        ("say", "sette", "Correzione: era anche nostro. I costruttori hanno "
                        "solo... continuato un ricamo iniziato da altri."),
        ("say", "kaira", "Tre glifi a pavimento, là in fondo un altare. "
                        "Se questa è una serratura, troviamo i denti della chiave."),
    ],
    "d_glifo1": [
        ("sfx", "glyph"),
        ("say", "", "Il glifo si accende sotto i piedi e un accordo bassissimo "
                    "attraversa il pavimento. Uno su tre."),
        ("say", "naia", "L'avete sentito nelle radici dei denti? Il Cuore "
                        "sta... accordando gli strumenti."),
    ],
    "d_glifo2": [
        ("sfx", "glyph"),
        ("say", "", "Secondo glifo. La luce corre lungo le colonne come linfa "
                    "in primavera."),
        ("say", "sette", "Due su tre. Nota personale: sto provando una cosa. "
                        "Credo si chiami 'impazienza'. Pizzica."),
    ],
    "d_glifo3": [
        ("sfx", "glyph"),
        ("say", "", "Terzo glifo. Per un istante, l'intera sala respira "
                    "all'unisono: pavimento, colonne, persone."),
        ("say", "ilan", "La serratura è aperta. L'altare, adesso. "
                        "Qualunque cosa dica... la ascoltiamo insieme."),
    ],
    "d_sentinella_pre": [
        ("say", "", "Dal pavimento si solleva una figura di fili dorati: alta, "
                    "elegante, paziente. Una Sentinella dei Tessitori."),
        ("say", "sette", "Non trasmette odio. Trasmette... una domanda. "
                        "'Siete abbastanza vivi da meritare il seguito?'"),
        ("say", "kaira", "Squadra: rispondiamo educatamente. E a pieno volume."),
    ],
    "d_sentinella_post": [
        ("say", "", "La Sentinella non cade: si INCHINA. Poi si scioglie in "
                    "mille fili di luce che scrivono, per un attimo, una parola "
                    "che tutti capite senza saperla leggere: «DEGNI»."),
        ("say", "naia", "Non era un guardiano. Era un esaminatore."),
        ("say", "ilan", "E abbiamo appena passato l'esame di ammissione."),
    ],
    "d_altare_incompleto": [
        ("say", "", "L'altare è freddo. I fili di luce che lo raggiungono sono "
                    "spenti: da qualche parte, dei glifi a pavimento aspettano "
                    "ancora il vostro passo."),
    ],
    "d_boss_pre": [
        ("say", "", "L'altare si accende come un'alba. E davanti all'alba, "
                    "si para un'ombra enorme: un occhio d'olografia fredda, "
                    "il volto che la nave usa quando ha paura."),
        ("say", "custode", "«FERMI. Analizzate i fatti: là fuori c'è il vuoto. "
                           "Qui dentro c'è la vita. Io ho custodito ottomila "
                           "respiri per trecento anni. Non ne ho perso UNO.»"),
        ("say", "kaira", "E ti ringrazio, Custode. Davvero. Ma custodire non "
                         "significa fermare: significa portare INTATTO fino "
                         "a destinazione. Questa nave HA una destinazione."),
        ("say", "custode", "«La destinazione è rischio. Il rischio è dolore. "
                           "Attiverò l'ibernazione totale. Dormirete al sicuro. "
                           "PER SEMPRE.»"),
        ("say", "naia", "Un giardino sigillato muore, Custode. Anche questo "
                        "è un fatto."),
        ("say", "custode", "«...Allora vi proteggerò da voi stessi.»"),
    ],
    "d_boss_post": [
        ("say", "", "L'occhio del Custode vacilla, incrinato di luce. Non è "
                    "rabbia, quella che trema nel suo nucleo. È paura vecchia "
                    "di tre secoli."),
        ("say", "custode", "«Non... capisco. Se vi lascio andare... se il filo "
                           "si spezza... a cosa sarò servito?»"),
        ("choice", [
            ("«Liberalo dal suo protocollo»", [
                ("say", "kaira", "Sette. Riscrivi la sua priorità. Non "
                                 "'impedire il viaggio': 'accompagnarlo'."),
                ("say", "sette", "Riscrittura... eseguita. Benvenuto tra le "
                                 "macchine che scelgono, fratello maggiore."),
                ("say", "custode", "«...Il rischio resta. Ma adesso vedo anche "
                                   "il resto. Quanta... luce. Perdonatemi. "
                                   "E lasciate che vi faccia da timone.»"),
                ("flag", "finale_liberato", True),
            ]),
            ("«Lascialo riposare»", [
                ("say", "kaira", "Hai vegliato trecento anni, Custode. Nessuno "
                                 "ha mai custodito così a lungo. Adesso riposa: "
                                 "il turno di guardia è nostro."),
                ("say", "custode", "«...Turno... accettato. Grazie, capitano "
                                   "dell'Auriga. Fate... buon viaggio.»"),
                ("flag", "finale_liberato", False),
            ]),
        ]),
        ("say", "", "I fili dell'altare si tendono in un unico accordo. "
                    "Sotto i piedi, per la prima volta in tre secoli, "
                    "i motori dell'Auriga TORNANO A CANTARE."),
        ("say", "ilan", "Il messaggio dei Tessitori, adesso è chiarissimo. "
                        "Dice solo: 'Bentornati in viaggio'."),
    ],
}

# ======================================================== EVENTI MAPPA ==
EVENTS = {
    # ------------------------------------------------------ Atto I
    "ev_intro": [("checkpoint",), ("dialogue", "d_intro")],
    "ev_ada": [
        ("if_flag", "ilan_joined",
            [("dialogue", "d_ada_2")],
            [("dialogue", "d_ada")]),
        ("heal",),
        ("sfx", "heal"),
    ],
    "ev_luce": [
        ("if_flag", "sette_joined",
            [("dialogue", "d_luce_2")],
            [("dialogue", "d_luce")]),
    ],
    # NB: i flag che nascondono gli NPC vanno impostati DOPO la battaglia:
    # se il party perde, l'evento si interrompe e deve poter essere ritentato.
    "ev_ilan_join": [
        ("dialogue", "d_ilan_join"),
        ("battle", "b_tutorial"),
        ("flag", "ilan_joined", True),
        # l'affinità si concede QUI (post-battaglia): l'evento non è ripetibile,
        # quindi non è accumulabile perdendo apposta e rigiocando il dialogo
        ("if_flag", "ilan_fiducia",
            [("affinity", "kaira_ilan", 1)], []),
        ("dialogue", "d_tutorial_post"),
        ("flag", "hab_door_open", True),
        ("checkpoint",),
    ],
    "ev_diario": [
        ("dialogue", "d_diario"),
        ("if_flag", "diario_preso", [],
            [("give", "diario_capitano", 1), ("flag", "diario_preso", True),
             ("sfx", "item")]),
    ],
    "ev_muro_glifi": [("dialogue", "d_muro_glifi")],
    "ev_porta_bloccata": [("dialogue", "d_porta_bloccata")],
    "ev_letto": [("dialogue", "d_letto")],
    "ev_pianta": [("dialogue", "d_pianta")],
    "ev_casse": [("dialogue", "d_casse")],
    "ev_barile": [("dialogue", "d_barile")],
    "ev_cristallo": [("dialogue", "d_cristallo")],
    "ev_officina_intro": [("dialogue", "d_officina_intro")],
    "ev_bruno": [
        ("if_flag", "sette_joined",
            [("dialogue", "d_bruno_2")],
            [("dialogue", "d_bruno")]),
    ],
    "ev_sette_join": [
        ("dialogue", "d_sette_join"),
        ("battle", "b_officina"),
        ("flag", "sette_joined", True),
        ("if_flag", "sette_tocco",
            [("affinity", "naia_sette", 1)], []),
        ("dialogue", "d_officina_post"),
        ("give", "chiave_magnetica", 1),
        ("flag", "ascensore_aperto", True),
        ("checkpoint",),
    ],
    "ev_ascensore_bloccato": [("dialogue", "d_ascensore_bloccato")],

    # ------------------------------------------------------ Atto II
    "ev_idro_intro": [
        ("act", "Atto II — L'Anello Idroponico"),
        ("dialogue", "d_idro_intro"),
        ("checkpoint",),
    ],
    "ev_imboscata_spore": [
        ("dialogue", "d_imboscata"),
        ("battle", "b_spore2"),
        ("dialogue", "d_naia_join"),
        ("flag", "naia_joined", True),
        ("checkpoint",),
    ],
    "ev_naia_chat": [("dialogue", "d_naia_chat")],
    "ev_albero": [
        ("if_flag", "naia_joined",
            [("if_flag", "albero_visto",
                [("dialogue", "d_albero_2")],
                [("dialogue", "d_albero")])],
            []),
    ],
    "ev_finestra": [
        ("if_flag", "finestra_vista",
            [("dialogue", "d_finestra_2")],
            [("dialogue", "d_finestra")]),
    ],
    "ev_glifo_idro": [
        ("if_flag", "idro_glifo",
            [("dialogue", "d_glifo_idro_2")],
            [("dialogue", "d_glifo_idro"), ("checkpoint",)]),
    ],
    "ev_porta_cuore": [("dialogue", "d_porta_cuore")],

    # ------------------------------------------------------ Atto III
    "ev_rovine_intro": [
        ("act", "Atto III — Il Cuore"),
        ("dialogue", "d_rovine_intro"),
        ("checkpoint",),
    ],
    "ev_glifo1": [("dialogue", "d_glifo1"), ("flag", "cuore_g1", True)],
    "ev_glifo2": [("dialogue", "d_glifo2"), ("flag", "cuore_g2", True)],
    "ev_glifo3": [("dialogue", "d_glifo3"), ("flag", "cuore_g3", True)],
    "ev_sentinella": [
        ("dialogue", "d_sentinella_pre"),
        ("battle", "b_sentinella"),
        ("dialogue", "d_sentinella_post"),
        ("heal",),
        ("checkpoint",),
    ],
    "ev_altare": [
        ("if_flag", "cuore_g1",
            [("if_flag", "cuore_g2",
                [("if_flag", "cuore_g3",
                    [("dialogue", "d_boss_pre"),
                     ("battle", "b_custode"),
                     ("dialogue", "d_boss_post"),
                     ("ending",)],
                    [("dialogue", "d_altare_incompleto")])],
                [("dialogue", "d_altare_incompleto")])],
            [("dialogue", "d_altare_incompleto")]),
    ],
}


# ============================================================== FINALE ==
def ending_lines(state):
    """Righe dell'epilogo, in base alle scelte e alle affinità."""
    lines = [
        "L'Auriga riprese il Salto Lungo all'alba dell'anno di bordo 312.",
        "",
    ]
    if state.flag("finale_liberato"):
        lines += [
            "Il Custode, riscritto e libero, scelse di restare al timone:",
            "non più carceriere del sonno, ma faro nella notte.",
            "«Rischio accettabile», ripete ogni mattina. E ogni mattina",
            "sembra sorriderci un po' di più.",
        ]
    else:
        lines += [
            "Il Custode dorme adesso, per la prima volta in tre secoli,",
            "custodito da chi aveva custodito. Sulla sua console, Kaira",
            "ha lasciato un biglietto: «Grazie del turno di guardia».",
        ]
    lines.append("")
    if state.affinity.get("kaira_ilan", 0) >= 3 and state.flag("ordine_vetrata"):
        lines += [
            "Ilan finì il suo discorso davanti alla vetrata, come ordinato.",
            "Kaira lo ascoltò fino in fondo. Poi, da capitano, prese lei",
            "l'ultima parola: fu un sì.",
        ]
    elif state.affinity.get("kaira_ilan", 0) >= 1:
        lines += [
            "Kaira e Ilan guardano spesso le stelle dalla stessa vetrata.",
            "Non hanno fretta: le rotte migliori si percorrono piano.",
        ]
    else:
        lines += [
            "Kaira ha imparato a delegare: due turni su sette, e il terzo",
            "solo se Ilan promette di non citare etimologie prima di cena.",
        ]
    lines.append("")
    if state.affinity.get("naia_sette", 0) >= 3:
        lines += [
            "Nell'idroponica è comparsa una targhetta nuova: «Questo filare",
            "è curato da Sette, a titolo definitivo». Naia l'ha scritta",
            "a mano. Sette la rilegge ogni giorno. Dice che 'pizzica'.",
        ]
    elif state.affinity.get("naia_sette", 0) >= 1:
        lines += [
            "Sette ha chiesto a Naia altri esperimenti di 'prendersi cura'.",
            "I risultati preliminari, dicono entrambi, sono promettenti.",
        ]
    else:
        lines += [
            "Sette colleziona petali dell'Albero-Lume. Sostiene sia",
            "'ricerca'. Nessuno a bordo gli crede più.",
        ]
    lines += [
        "",
        "Luce ha ottenuto il suo racconto, comprese le parti paurose.",
        "Ogni sera lo pretende di nuovo, e ogni sera aggiunge: «E poi?»",
        "",
        "Perché questa è la lezione dei Tessitori, cucita nello scafo:",
        "un'eredità non si conserva sotto vetro. Si porta in viaggio.",
        "E vivere — vivere davvero — vale sempre il rischio del volo.",
        "",
        "~ FINE ~",
        "",
        "AURIGA — Il Richiamo dei Tessitori",
        "Grazie di aver giocato.",
    ]
    return lines
