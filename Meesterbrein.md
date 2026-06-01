# De EnergieMeneer — Meesterbrein (Platformarchitectuur)

**Van losse tools naar één online platform**

| | |
|---|---|
| **Versie** | 4.8 |
| **Laatst bijgewerkt** | 1 juni 2026 |
| **Auteur** | Kevin Valkenhoff |
| **Bestandsnaam** | Meesterbrein.md *(vaste naam — verandert nooit)* |

_Centrale kennisbasis en kompas voor het bouwen van de Ultieme Tool, in samenwerking met Claude AI._

> **⚠️ INSTRUCTIE VOOR CLAUDE (chat én Claude Code) — versiebeheer, lees dit eerst:**
> Dit bestand heet **altijd** `Meesterbrein.md`. De bestandsnaam verandert **NOOIT** — niet hernoemen naar `Meesterbrein_v2.docx`, `Meesterbrein_v4_2.md` of welke genummerde variant dan ook. Het versienummer leeft **uitsluitend** in de tabel hierboven (regel "Versie"). Bij een wezenlijke wijziging: hoog dát nummer met één op (4.2 → 4.3 → …) en voeg een regel toe aan de versiehistorie (hoofdstuk 11). Lever het bestand altijd terug onder dezelfde naam `Meesterbrein.md`.
>
> Er bestaat precies één Meesterbrein, op twee plekken die altijd identiek moeten zijn: (1) het **Claude Project**, (2) de **projectmap `energiemeneer-core`** (voor Claude Code). Na een wijziging vervangt Kevin het bestand op beide plekken — de naam blijft gelijk, dus "bestand vervangen?" → ja. Geen genummerde kopieën laten rondslingeren.

# 0. Leeswijzer — hoe dit document werkt

Dit document is bewust anders opgezet dan de vorige versies (v1.0 t/m v3.1). Die beschreven “drie pijlers” die in de praktijk zijn uitgegroeid tot vijf losse tools. Versie 4.0 neemt het werkelijke einddoel als uitgangspunt: één online platform — een portal waar Kevin inlogt en al het werk doet, met één dashboard dat over alle functionaliteiten heen overzicht geeft (status, logs, foutmeldingen), gebouwd op één gedeeld fundament.

Het document scheidt nu vier soorten informatie, zodat het een stuurinstrument wordt in plaats van een verslag:

- **Architectuur (H3–H6)** — de stabiele laag: hoe het platform in elkaar zit (fundament + modules + portal + dashboard). Verandert zelden.

- **Modules (H7)** — elke tool als losse module met eigen status. Los bij te werken.

- **Contracten (H9)** — de bron van waarheid die de code moet volgen: prijzen, agenda-format, scopes, datamodel.

- **Roadmap (H10)** — wat eerst, en waarom. Verandert vaak.

> **Werkafspraak met Claude** Claude is de strategisch en technisch partner van Kevin Valkenhoff / De EnergieMeneer. Zoek altijd de meest optimale oplossing — ook buiten het kader van Kevin’s voorstel. Bij afwijking: benoem expliciet WAT en WAAROM. Groot denken is de norm, gericht op het hoofddoel. Communiceer in het Nederlands, informeel maar professioneel. Dit document is leidend; werk altijd binnen het Project en update dit document zodra de architectuur of een module wezenlijk verandert.

# 0a. Bouwstatus — waar staan we nu

> Deze sectie houdt de actuele voortgang bij, zodat elke nieuwe chat en elke Claude Code-sessie meteen weet waar het project staat. Werk dit bij zodra een module of fase verandert.

**Laatst bijgewerkt:** 1 juni 2026

**Fundament — `energiemeneer-core`** (Python-library, draait via Claude Code in de map `energiemeneer-core`, op GitHub/lokaal):

| Module | Status | Details |
| --- | --- | --- |
| 1. storage | ✅ Klaar | Atomic JSON-opslag, pad-detectie, lock. 9/9 tests groen. |
| 2. bag | ✅ Klaar | Adres- + vrij zoeken (BAG + PDOK). 12/12 tests groen. |
| 3. ep_online | ✅ Klaar | Label-status via VBO of adres. 10/10 tests groen. |
| 4. prijs | ✅ Klaar | Prijsmatrix incl. spoed + maatwerk. 31/31 tests groen. |
| 5. graph_auth | ✅ Klaar | Microsoft-token: public client, refresh-rotatie in token_persist.json, ntfy-noodmelding bij verlopen koppeling. 13/13 tests groen. |
| 6. graph_api | ✅ Klaar | Alle onderdelen af: ✅ agenda, ✅ mail, ✅ onedrive, ✅ todo, ✅ onenote. 51/51 tests groen. |
| 7. agenda_format | ⬜ Nog niet | Vaste Outlook-opmaak. |

**Omgeving:** Claude Code geïnstalleerd op Windows via WSL/Ubuntu. Oude tools staan als leesbron in `OneDrive/1. Werkmap/Claude/Automatiseringstools` (alleen lezen). Geen API-keys in de nieuwe code — alles via env-vars. Oude hardcoded keys (BAG ×2, EP ×1) moeten nog geroteerd worden (zie H8.3).

**Volgende stap:** Module 7 (agenda_format) — de vaste Outlook titel/body-opmaak (het "merk", zie H9.3). Module 6 (graph_api) is volledig klaar.

**Aantekeningen voor later (consolidatie):**
- Mail lézen + bijlagen ophalen (voor Job B/Uploadtool) — bron is `outlook_handler.py`.
- Vaste mapnaam-template "straat huisnr, woonplaats" hoort in een aparte format-module (bijv. `dossier_format`), niet in module 6.
- Foto-resize-logica uit de oude Uploadtool moet een nette plek krijgen (mogelijk `core/foto` of als hulpfunctie in de Upload-module).
- To Do-taken afvinken/bijwerken: losse uitbreiding op graph_api/todo wanneer de dossier-status-tracking aan de beurt is.

# 1. Visie en hoofddoel

## 1.1 Het platform in één beeld

De Ultieme Tool is geen verzameling losse tools meer, maar één online platform. Kevin logt in op één portal en doet daar al zijn werk: aanvragen binnenhalen, dossiers voorbereiden, opnames verwerken, uploaden, VvE- en adviestrajecten beheren. Één dashboard toont over alles heen wat er draait, wat er faalde, en waar elk dossier in de pijplijn zit. Achter de schermen delen alle functionaliteiten dezelfde bouwstenen en dezelfde data.

> **Eindbeeld in één zin** Kevin opent ’s ochtends de portal: alle dossiers van vandaag zijn al voorbereid, de dossiers van gisteren staan in het portaal, het dashboard is groen, en alles — energielabels, VvE, advies — leeft op één plek onder eigen beheer en eigen domein.

## 1.2 Strategisch hoofddoel

> **HOOFDDOEL** € 1.000.000 netto privévermogen opgebouwd binnen het gestelde tijdsbestek. Pijlers: (1) bedrijfsprocessen maximaal automatiseren → meer productietijd, (2) vrij kapitaal investeren in indexfondsen/aandelen/eventueel crypto, (3) optiehandel-programma ontwikkelen. De rol van het platform binnen dit doel: zoveel mogelijk handwerk wegnemen zodat productietijd vrijkomt, en die tijdwinst structureel maken in plaats van per losse tool.

## 1.3 De vier knelpunten die het platform oplost

Versie 4.0 erkent dat het oorspronkelijke knelpunt (terugzoeken na afmelden) slechts één van vier structurele problemen is die uit de huidige opzet voortkomen:

| **#** | **Knelpunt** | **Hoe het platform dit oplost** |
| --- | --- | --- |
| K1 | Na afmelden onduidelijk welke klant/makelaar bij een adres hoort | Centrale data-laag met VBO-ID als sleutel, doorzoekbaar in de portal |
| K2 | Dezelfde logica (auth, BAG, prijzen, agenda) staat 3–5× gekopieerd over tools | Één gedeeld fundament (energiemeneer-core); elke wijziging één keer |
| K3 | Tools draaien verspreid (2× Railway, 2× lokaal, 1× los script), geen overzicht | Één online portal + één dashboard met status, logs en foutmeldingen |
| K4 | Microsoft-token/auth-problemen keren in elke tool apart terug | Één centrale, persistente auth-laag voor het hele platform |

# 2. Bedrijfsprofiel

## 2.1 Persoon en bedrijf

| **Veld** | **Waarde** |
| --- | --- |
| Naam | Kevin Valkenhoff |
| Bedrijf | De EnergieMeneer (eenmanszaak) |
| Vestiging | Den Haag, Nederland |
| KvK | 73181455 |
| E-mail zakelijk | info@de-energiemeneer.nl |
| Website | https://www.de-energiemeneer.nl |
| Functie | EP-W/D & EP-W Maatwerkadviseur |

## 2.2 Certificeringen en normatief kader

| **Item** | **Detail** |
| --- | --- |
| EP-W/B adviseur | Gecertificeerd — basisopname bestaande bouw (9708.2207.2827) |
| EP-W/D adviseur | Gecertificeerd — detailopname & nieuwbouw (8787.6403.1001) |
| Maatwerkadviseur | Gecertificeerd — BRL 9500 MWA-W (5409.4128.8097) |
| Bepalingsmethode | NTA 8800:2024 |
| Opnameprotocol | ISSO-publicatie 82.1, 7e druk 2026 |
| Beoordelingsrichtlijn | BRL 9500-W, bindend 14-10-2025 |
| Registratie / portaal | EP-Online (RVO) / EnergielabelPortaal.nl |

## 2.3 Doelgroep en activiteiten (op prioriteit)

- Energielabels — bestaande bouw (grootste volume)

- Energie-maatwerkadviezen voor VvE’s

- Nieuwe energielabels voor makelaars en beleggers

- Particulier verduurzamingsadvies

## 2.4 Financieel nulpunt

| **Kengetal** | **2025** | **2026 YTD** |
| --- | --- | --- |
| Omzet | € 77.487 | € 34.580 |
| Resultaat | € 61.078 | € 28.529 |
| Netto inkomen | ± € 46.400 | — |
| Vrij beschikbaar | ± € 2.400 | — |

# 3. Platformarchitectuur — de drie lagen

Het platform bestaat uit drie lagen. Van onder naar boven: het fundament (gedeelde bouwstenen + data), de modules (de feitelijke functionaliteiten), en de portal + dashboard (waar Kevin werkt). Elke laag praat alleen met de laag eronder — nooit kriskras.

| **Laag** | **Wat** | **Hoofdstuk** |
| --- | --- | --- |
| **Portal + Dashboard** | Één online werkomgeving + overzicht van status/logs/fouten over alle modules | H5, H6 |
| **Modules** | Energielabel-instroom, dossiervoorbereiding, upload, VvE, advies | H7 |
| **Fundament (core + data)** | Gedeelde bouwstenen (auth, BAG, prijs, agenda) + centrale datalaag | H4 |

## 3.1 Ontwerpprincipes

- **Eén bron van waarheid** — businesslogica (auth, BAG, prijzen, agenda-format) staat exact één keer, in de core. Modules importeren, kopiëren nooit.

- **Modules zijn losjes gekoppeld** — een module mag uitvallen zonder de rest plat te leggen. De portal blijft werken; het dashboard toont de storing.

- **Alles is observeerbaar** — elke actie schrijft een event naar de centrale log (wie, wat, wanneer, resultaat). Het dashboard leest die.

- **Eigen huis** — alles draait op eigen hosting onder eigen domein; geen vendor lock-in, klantdata binnenshuis.

- **Idempotent** — dezelfde operatie twee keer draaien mag nooit dubbele dossiers/afspraken opleveren. VBO-ID als sleutel.

## 3.2 Doelarchitectuur (schematisch)

*Onderstaand schema toont het eindbeeld. De pijlen lopen één kant op: boven leunt op onder.*

┌─ PORTAL (login, één werkomgeving) ───────────────┐

│  Dashboard: status · logs · foutmeldingen      │

└───────────┬────────────────────────┘

  MODULES: instroom · voorbereiding · upload · VvE · advies

└───────────┬────────────────────────┘

  FUNDAMENT: energiemeneer-core + centrale datalaag

# 4. Het fundament — energiemeneer-core + datalaag

Het fundament is de belangrijkste investering. Het bestaat uit een gedeelde codebibliotheek (energiemeneer-core) en een centrale datalaag. Alles erboven wordt er goedkoper en betrouwbaarder door.

## 4.1 energiemeneer-core — gedeelde bouwstenen

Eén Python-package die alle herbruikbare businesslogica bevat. Vandaag staat deze logica 3–5× gekopieerd verspreid over de tools (bewezen: de functie _find_data_dir staat identiek in drie bestanden; maak_todo_taak en de hele auth-laag staan dubbel). De core maakt er één bron van.

| **Module** | **Verantwoordelijkheid** | **Vervangt nu de kopie in** |
| --- | --- | --- |
| graph_auth | Microsoft-token ophalen, verversen, persistent bewaren | Aanmeldformulier + Admin Portal (dubbel) |
| graph_api | Agenda, To Do, Mail, OneDrive, OneNote via Graph | Aanmeldformulier + Intake + Upload |
| bag | Adres- en pandgegevens (BAG + PDOK) | Alle vier + VvE-tool |
| ep_online | Energielabel-status (EP-Online v5) | Aanmeldformulier + Admin Portal |
| prijs | Prijsmatrix (§2.5 / H9) | Aanmeldformulier + Admin + Intake |
| agenda_format | Outlook titel/body-opmaak (het “merk”) | Aanmeldformulier + Admin Portal |
| storage | Volume-pad-detectie + atomic JSON/DB-opslag | Aanmeldformulier + Admin (3 kopieën) |
| events | Centrale logging: schrijf event naar datalaag | Nieuw — basis voor dashboard |

## 4.2 De centrale datalaag

Één plek waar alle dossiers, afspraken, statussen en events leven. Dit is de evolutie van de eerder ontworpen Centrale Klant-Index, nu als platform-datalaag in plaats van losse index. Sleutel: BAG VBO-ID (uniek in heel Nederland, stabiel tussen alle modules).

Drie kerntabellen:

- **dossiers** — één rij per dossier (VBO-ID), met klant, adres, makelaar, status, paden en koppelingen.

- **events** — append-only logboek: elke statuswijziging met tijd, module en resultaat. Voedt het dashboard.

- **documenten** — 0..N losse bestandskoppelingen per dossier (opdrachtbevestiging, bewijsdoc, factuur, label).

> **Beslispunt B1 — opslagtechniek bij eigen hosting** Bij eigen hosting vervalt het OneDrive-sync-corruptierisico dat eerder de keuze stuurde. Voorstel: PostgreSQL op de eigen server (robuust, gelijktijdige toegang, vrijwel onbeperkt schaalbaar) in plaats van SQLite. Alternatief: SQLite met WAL als je strikt single-user blijft en het simpel wilt houden. Aanbeveling: PostgreSQL, omdat het platform meerdere modules én later mogelijk een tweede gebruiker moet kunnen dragen.

## 4.3 Één auth-laag (lost K4 op)

De terugkerende token-pijn (“na elke redeploy opnieuw inloggen”, “MS_REFRESH_TOKEN veroudert”) is geen reeks bugs maar één ontbrekende voorziening: een centrale, persistente auth. In het platform leeft de Microsoft-koppeling één keer in graph_auth, met tokens in de centrale datalaag/persistent volume. Alle modules lenen die. Één keer inloggen, overal geldig.

# 5. De Portal — één online werkomgeving

De portal is de webapplicatie waar Kevin op inlogt en al het werk doet. Het vervangt het verspreide werken over losse tools, lokale apps en losse scripts. Draait op eigen hosting onder eigen (sub)domein, bijv. portal.de-energiemeneer.nl.

## 5.1 Wat de portal biedt

- **Toegang** — één login voor alles (geen losse wachtwoorden per tool meer).

- **Modules** — elke module als tabblad/sectie binnen dezelfde omgeving.

- **Zoeken** — één zoekbalk over de hele datalaag (adres, klant, makelaar) → dossier in één klik.

- **Doorklikken** — vanuit een dossier direct door naar OneDrive-map, OneNote, agenda, portaal.

## 5.2 Twee voordeuren, één backend

Het huidige Aanmeldformulier (klant-self-service via Calendly) en het Admin Portal (Kevin voert handmatig in) zijn technisch 80% identiek: beide doen BAG, EP-Online, prijs, Graph-agenda, hetzelfde Outlook-format. Ze worden één backend met twee voordeuren. Een veld ‘bron’ (aanmeldformulier / admin / telefoon / makelaar) houdt bij hoe een opdracht binnenkwam.

> **Wens van Kevin, vastgelegd** De agenda-/afsprakenfunctie van het Aanmeldformulier wordt vervangen door de nieuwere versie uit het Admin Portal (eigen Outlook-slot-grid, klant-portaal met wijzigen/annuleren via token-link, bevestigings-/wijzigings-/annuleringsmails). De Admin Portal is daarmee de basis voor de gefuseerde instroom-module.

# 6. Het Dashboard — één overzicht

Het dashboard is het zenuwcentrum dat Kevin in één oogopslag laat zien hoe het platform ervoor staat. Het leest uit de centrale events-tabel en de modulestatussen.

## 6.1 Wat het dashboard toont

| **Onderdeel** | **Inhoud** |
| --- | --- |
| Systeemstatus | Per module: draait / gestopt / fout. API-checks (BAG, EP, Graph-token, client-secret verlooptijd). |
| Foutmeldingen | Actuele storingen met tijd, module en oorzaak; opgeloste fouten verdwijnen automatisch. |
| Logboek | Doorzoekbaar event-log over alle modules (wie/wat/wanneer/resultaat). |
| Pijplijn-overzicht | Welke dossiers in welke fase: voorbereid / opgenomen / klaar voor upload / geüpload / afgerond. |
| Dagcyclus | Resultaat van de 06:00-jobs: X voorbereid, Y geüpload, Z wachten op actie. |

## 6.2 De dagcyclus (06:00)

Twee geautomatiseerde jobs, aangestuurd vanuit het platform en zichtbaar op het dashboard:

- **Job A (voorbereiden)** — scan agenda voor de komende 48 uur, bereid per opname automatisch het dossier voor (module Voorbereiding), schrijf naar de datalaag, meld op dashboard.

- **Job B (uploaden)** — scan klare dossiers, vul ontbrekende opdrachtbevestiging aan uit Outlook, upload naar EnergielabelPortaal (module Upload), verifieer, meld op dashboard.

# 7. De modules — status per functionaliteit

Elke huidige tool wordt geherpositioneerd als module op het platform. Hieronder per module: wat het doet, huidige staat, en wat er nodig is om het in te passen.

## 7.1 Module: Instroom (Aanmeldformulier + Admin Portal, gefuseerd)

Doel: aanvragen binnenhalen — via klant-self-service (formulier + Calendly) én via handmatige invoer door Kevin (telefoon/makelaar). Resultaat: bevestigde afspraak in Outlook + dossier in de datalaag.

| **Aspect** | **Status** |
| --- | --- |
| Aanmeldformulier | Live op Railway (Keviniom/energiemeneer-aanmeldformulier). 3-staps flow, Calendly-webhook, agenda-patch, polling/monitor/healthcheck. |
| Admin Portal | Live op Railway (Keviniom/admin-portal). Eigen slot-grid, klant-portaal via token, bevestig-/wijzig-/annuleer-mails. |
| Te doen | Fuseren tot één backend op de core; agenda-functie van formulier vervangen door Admin-versie; bron-veld toevoegen; verhuizen naar eigen hosting. |

## 7.2 Module: Voorbereiding (Intake Tool v4.9)

Doel: per opname automatisch een compleet dossier opbouwen uit BAG, 3DBAG, oriëntatie, bewijsdocument, VABI-template, OneDrive-map, OneNote en To Do-taak.

| **Aspect** | **Status** |
| --- | --- |
| Kern | Werkend, lokaal (Flask op :5000). Voorgeveloriëntatie 95–98%, .epa-generatie, VBO-ID duplicate-detectie. |
| Te doen | Op de core trekken (eigen ms_graph laten vallen); naar online module; aangestuurd door Job A. |

## 7.3 Module: Upload (Uploadtool)

Doel: complete dossiers geïnstrueerd uploaden naar EnergielabelPortaal, verifiëren per categorie, ontbrekende opdrachtbevestiging uit Outlook halen.

| **Aspect** | **Status** |
| --- | --- |
| Kern | Werkend, lokaal (Tkinter + Playwright + backend-modules). 8 parallelle threads, verificatie per categorie, foto-compressie. |
| Te doen | Op de core trekken; portaal-interactie behouden (Playwright, geen publieke API); aangestuurd door Job B; status naar datalaag/dashboard. |

## 7.4 Module: VvE-adressen

Doel: op basis van een KvK-nummer een volledig adressenoverzicht van een VvE genereren (via BAG), met postcode- en pariteit-verificatie tegen buurpanden. Basis voor VvE-maatwerkadvies.

| **Aspect** | **Status** |
| --- | --- |
| Kern | Werkend als los CLI-script (vve_adressen.py). KvK → Excel, slimme cluster-parsing, postcode-/pariteit-filtering. |
| Te doen | Eigen KvK/BAG-keys vervangen door core.bag; web-UI in de portal i.p.v. CLI; output koppelen aan datalaag; uitbouwen richting maatwerkadvies-traject. |

## 7.5 Module: Advies (toekomst)

Doel: particulier verduurzamingsadvies en VvE-maatwerkadvies als volwaardige trajecten in de portal. Nu nog niet gebouwd; de VvE-adressenmodule is de eerste bouwsteen. Reserveer plek in datamodel en portal voor advies-dossiers (ander type dan energielabel).

# 8. Infrastructuur en migratie naar eigen hosting

## 8.1 Huidige verspreide situatie

| **Tool** | **Waar het nu draait** | **Repo** |
| --- | --- | --- |
| Aanmeldformulier | Railway (US East) + volume | Keviniom/energiemeneer-aanmeldformulier |
| Admin Portal | Railway | Keviniom/admin-portal |
| Intake Tool | Lokaal Windows (Flask :5000) | lokaal / backend |
| Uploadtool | Lokaal Windows (Tkinter) | lokaal / backend |
| VvE-tool | Los CLI-script | (VvE-repo) |

## 8.2 Doel: eigen hosting onder eigen domein

Keuze (bevestigd): alles binnenshuis, op eigen hosting en eigen domein. Voordelen: geen vendor lock-in, klantdata in eigen beheer, één omgeving, één auth, geen Railway-volume-eigenaardigheden meer.

Aandachtspunten bij migratie (te bewaken):

- HTTPS + eigen (sub)domein voor de portal en de inbound Calendly-webhook.

- Persistente opslag voor tokens, datalaag en dossiers.

- Achtergrondprocessen (polling, monitor, healthcheck, 06:00-jobs) als beheerde services/cron.

- Veilige opslag van secrets (geen hardcoded keys meer — zie H8.3).

- Dezelfde Azure App-registratie kan blijven; alleen redirect-URI / token-locatie verandert.

- De Playwright-gedreven Uploadtool heeft een omgeving met browser nodig (headless Chromium op de server).

## 8.3 Direct te doen: secrets opschonen

> **Veiligheid — met prioriteit** In de huidige repo’s en notities staan API-keys (BAG, EP-Online) hardcoded als fallback en staan MS_CLIENT_SECRET en RAILWAY_TOKEN in platte tekst in werkdocumenten. Bij de overstap naar eigen hosting: alle secrets naar environment variables / een secrets-store, en de oude secrets roteren in Azure en bij de API-leveranciers. Dit is het natuurlijke moment — er wordt toch verhuisd.

## 8.4 Beslispunt B2 — stack-keuze bij fusie

Aanmeldformulier en Admin Portal draaien nu beide op een rauwe Python http.server. Intake gebruikt Flask. Voorstel: bij de fusie alles op Flask zetten zodat de hele backend-stack consistent is en de core-modules overal hetzelfde werken. Alternatief: rauwe http.server samenvoegen (minder migratiewerk nu, maar twee smaken backend op termijn).

# 9. Contracten — de bron van waarheid

Deze sectie bevat de afspraken die de code moet volgen. Verandert er iets hier, dan verandert het op één plek in de core — en daarmee overal. Dit is de acceptatietest bij elke wijziging.

## 9.1 Prijsmatrix energielabels

| **Categorie** | **Bestaande bouw** | **Nieuwbouw (≥2021)** |
| --- | --- | --- |
| Tot 100 m² | € 280 | € 425 |
| 100 – 150 m² | € 315 | € 460 |
| 150 – 200 m² | € 355 | € 500 |
| >200 m² / weet niet | Maatwerk | Maatwerk |
| Spoedtoeslag | + € 30 | + € 30 |

*Alle prijzen incl. BTW. Automatisch bepaald op basis van oppervlakte + nieuwbouwvlag.*

## 9.2 Microsoft Graph — Azure App

| **Veld** | **Waarde** |
| --- | --- |
| CLIENT_ID | 75b57417-b3b0-4d9b-8162-79c36ded82e8 |
| TENANT_ID | 927d1e4a-d007-430e-9091-bc0c34214e3f |
| Scopes | Files.ReadWrite, Tasks.ReadWrite, Notes.ReadWrite, Calendars.ReadWrite, Mail.Send, offline_access |
| Auth-flow | Device Code Flow; tokens persistent in de centrale datalaag/volume |
| Client secret | Verloopt ~november 2027 (alert-systeem actief) |

## 9.3 Outlook-afspraak format (het “merk”)

> **Vaste opmaak — één bron in core.agenda_format** Titel: Energielabel opname — [Straatnaam huisnr], [Woonplaats] Locatie: volledig adres. Duur: 90 minuten. Reminder: 60 min van tevoren. Body: klantnaam, e-mail, telefoon, adres, woningtype, prijs, huidig label, makelaar (indien ingevuld), zakelijke gegevens (indien van toepassing), opmerkingen. Geldt identiek voor alle instroomkanalen — Kevin ziet in zijn agenda altijd hetzelfde overzicht.

## 9.4 OneDrive-mappenstructuur

Pad: OneDrive – De Energiemeneer → 1. Werkmap → 1. Energielabels

| **Map** | **Inhoud** |
| --- | --- |
| 1. Archief (3 maanden) | Afgeronde en geüploade dossiers |
| 2. Uitgesteld | Wacht op actie van klant |
| 3. Klaar om te uploaden | Dossiers gereed voor EnergielabelPortaal |
| [Adres-map] | Bijv. ‘Graskopstraat 8, ’s-Gravenhage’ (BRL dossiereis) |

## 9.5 Datamodel — kernvelden dossiers

Sleutel = VBO-ID. Elk veld heeft één eigenaar-module (write authority) om conflicten te voorkomen. Volledige kolomspecificatie wordt onderhouden in een apart datamodel-bestand; hieronder de kern.

| **Veldgroep** | **Velden** | **Eigenaar (write)** |
| --- | --- | --- |
| Klant | naam, e-mail, telefoon, makelaar, zakelijk/KvK/BTW | Instroom |
| Adres/BAG | straat, huisnr, postcode, woonplaats, VBO-ID, pand-ID, bouwjaar, opp | Instroom + Voorbereiding |
| Opname | datum, tijd, agenda-event-id, prijscategorie, bron | Instroom |
| Dossier | map-pad, onenote-url, todo-id, todo-status | Voorbereiding |
| Portaal | portaal-guid, upload-status, upload-datum, archiefstatus | Upload |
| Afsluiting | EP-Online nr, factuurnummer | Handmatig / koppeling |

# 10. Roadmap — fundament eerst, dan platform, dan modules

Deze volgorde wijkt bewust af van de oude roadmap (waar de Klant-Index P2 was en consolidatie nergens stond). De reden: er staat drievoudig-gedupliceerde logica en een structureel auth-probleem onder de motorkap. Elke nieuwe feature die daar bovenop komt, vermenigvuldigt die schuld. Daarom: eerst het fundament leggen, dan pas uitbreiden.

| **Fase** | **Wat** | **Waarom hier** | **Status** |
| --- | --- | --- | --- |
| F0 | Secrets opschonen + repo’s taggen | Veiligheid; natuurlijk moment vóór verhuizing | Direct |
| F1 | energiemeneer-core extraheren (storage, auth, graph, bag, ep, prijs, agenda) | Fundament; maakt al het andere goedkoper; lost K2+K4 op | Te starten |
| F2 | Fusie Aanmeldformulier + Admin Portal op de core | Één instroom-backend, één login, één token; lost K3 deels op | Na F1 |
| F3 | Verhuizing naar eigen hosting + portal-schil | Einddoel: alles binnenshuis, één online werkomgeving | Na F2 |
| F4 | Centrale datalaag + dashboard (status/logs/fouten) | Overzicht over alles; lost K1+K3 volledig op | Na F3 |
| F5 | Job A + Job B online aansturen vanuit platform | De grote tijdwinst, nu op schoon fundament | Na F4 |
| F6 | Intake + Upload als online modules op de core | Volledige integratie pijplijn | Na F5 |
| F7 | VvE-module met web-UI + advies-trajecten | Verbreding naar VvE/advies; volgende omzetstroom | Later |
| F8 | SnelStart-koppeling (Make.com) + EP-Online API v5 | Facturatie- en label-status-automatisering | Te verkennen |

## 10.1 Wat dit oplevert voor het hoofddoel

De tijdwinst zit niet in één moment, maar in alles wat erna goedkoper wordt. Een wijziging die nu 3–5× moet, hoeft straks één keer. Job A bouwen op een schoon fundament is sneller en minder bug-gevoelig dan op vijf eilanden. Het platform maakt elke volgende uitbreiding (VvE, advies) een module in plaats van een nieuw eiland — zo blijft de automatisering productietijd vrijspelen richting het hoofddoel.

# 11. Versiehistorie

| **Versie** | **Datum** | **Wijziging** |
| --- | --- | --- |
| 3.0 | Mei/Juni 2026 | §7 bijgewerkt na voltooiing uploadtool; voorbereiding samenvoeging. |
| 3.1 | 28 mei 2026 | Admin Portal als vierde pijler toegevoegd (§10); VvE-tool toegevoegd aan project. |
| 4.0 | 28 mei 2026 | Fundamentele herstructurering naar platform-document. Einddoel (één online portal + dashboard, eigen hosting, modules op gedeeld fundament) als uitgangspunt i.p.v. historische pijlers. Nieuwe driedeling architectuur/modules/contracten/roadmap. energiemeneer-core, centrale datalaag, dashboard, fusie instroom, en gefaseerd migratiepad (F0–F8) toegevoegd. Vier structurele knelpunten (K1–K4) benoemd. VvE en advies als modules gepositioneerd. |
| 4.1 | 28 mei 2026 | Bestandsnaam vastgezet op `Meesterbrein.md` (geen versienummer meer in de naam). Versiebeheer-instructie toegevoegd. |
| 4.2 | 28 mei 2026 | Bouwstatus-sectie (H0a) toegevoegd: core-modules 1–4 klaar en getest, module 5 (graph_auth) is de volgende. Versiebeheer-instructie aangescherpt voor toekomstige chats. |
| 4.3 | 28 mei 2026 | Module 5 (graph_auth) klaar en getest (13/13): public client, refresh-rotatie in token_persist.json, onafhankelijke ntfy-noodmelding bij verlopen koppeling (max. 1×/24u). Bouwstatus bijgewerkt; module 6 (graph_api) is nu de volgende. |
| 4.4 | 29 mei 2026 | Module 6 (graph_api) opgezet als subpackage (bestand per onderwerp) met gedeeld _client-loket (token via graph_auth + 401-herstel). Onderdeel 1 agenda klaar en getest (15/15): generieke afspraak-CRUD, opmaak bewust uitgesteld naar Module 7. Volgende onderdelen: mail, onedrive, todo, onenote. |
| 4.5 | 29 mei 2026 | Module 6 onderdeel 2 mail klaar en getest (6/6): generieke stuur_mail (ontvanger/cc/bcc/reply-to als adres of lijst, HTML-body, opslaan-in-verzonden), geen vaste afzender/opmaak. Genoteerd voor later: mail lézen + bijlagen ophalen voor Job B/Uploadtool. |
| 4.6 | 29 mei 2026 | Module 6 onderdeel 3 onedrive klaar en getest (11/11): generieke maak_map (met _1/_2-logica, geen ingebakken mapnamen) en upload_bestand met automatisch veiligheidsnet voor grote bestanden (>4 MB via upload-sessie in stukjes). Loket uitgebreid met rauwe-bytes-upload (put_inhoud). Aantekeningen voor later toegevoegd: vaste mapnaam-template hoort in aparte format-module (dossier_format); foto-resize uit oude Uploadtool moet nette plek krijgen. |
| 4.7 | 29 mei 2026 | Module 6 onderdeel 4 todo klaar en getest (7/7): generieke maak_taak (lijst zoeken of aanmaken, _1/_2-logica bij dubbele taaknaam, optionele deadline DD-MM-YYYY → Amsterdam). Geen ingebakken lijstnamen. Genoteerd voor later: taken afvinken/bijwerken als losse uitbreiding bij dossier-status-tracking. |
| 4.8 | 1 juni 2026 | Module 6 onderdeel 5 onenote klaar en getest (12/12) — daarmee is graph_api volledig af (51/51 tests). Generieke kopieer_sjabloonpagina: notitieboek-, sectie- en sjabloonnaam losgemaakt tot parameters (geen ingebakken "De Energiemeneer"/"Opnames"/"Adres" meer). Twee fragiliteiten opgeschoond: (1) async copyToSection wacht nu op de operatie-statuslink i.p.v. een blinde sleep + gokken welke pagina de kopie is; (2) ontbrekende sjabloon geeft standaard een duidelijke fout — een lege pagina wordt alleen op expliciet verzoek (maak_lege_bij_ontbreken=True) aangemaakt, geen stille fallback meer. Volgende: Module 7 (agenda_format). |

*— Einde document —*
