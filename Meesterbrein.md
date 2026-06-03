# De EnergieMeneer — Meesterbrein (Platformarchitectuur)

**Van losse tools naar één online platform**

| | |
|---|---|
| **Versie** | 4.16 |
| **Laatst bijgewerkt** | 3 juni 2026 |
| **Auteur** | Kevin Valkenhoff |
| **Bestandsnaam** | Meesterbrein.md *(vaste naam — verandert nooit)* |

_Centrale kennisbasis en kompas voor het bouwen van de Ultieme Tool, in samenwerking met Claude AI._

> **⚠️ INSTRUCTIE VOOR CLAUDE (chat én Claude Code) — versiebeheer, lees dit eerst:**
> Dit bestand heet **altijd** `Meesterbrein.md`. De bestandsnaam verandert **NOOIT** — niet hernoemen naar `Meesterbrein_v2.docx`, `Meesterbrein_v4_2.md` of welke genummerde variant dan ook. Het versienummer leeft **uitsluitend** in de tabel hierboven (regel "Versie"). Bij een wezenlijke wijziging: hoog dát nummer met één op (4.2 → 4.3 → …) en voeg een regel toe aan de versiehistorie (hoofdstuk 11). Lever het bestand altijd terug onder dezelfde naam `Meesterbrein.md`.
>
> Er bestaat precies één Meesterbrein, en die leeft op één plek: de **projectmap `energiemeneer-core`** (op GitHub). Het gekoppelde **Claude Project** leest het bestand **live vanuit GitHub** — na een push hoeft Kevin dus niets handmatig te uploaden of te vervangen. Eén bron van waarheid, geen genummerde kopieën laten rondslingeren.

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

**Laatst bijgewerkt:** 3 juni 2026

**Fundament — `energiemeneer-core`** (Python-library, draait via Claude Code in de map `energiemeneer-core`, op GitHub/lokaal):

| Module | Status | Details |
| --- | --- | --- |
| 1. storage | ✅ Klaar | Atomic JSON-opslag, pad-detectie, lock. 9/9 tests groen. |
| 2. bag | ✅ Klaar | Adres- + vrij zoeken (BAG + PDOK). 12/12 tests groen. |
| 3. ep_online | ✅ Klaar | Label-status via VBO of adres. 10/10 tests groen. |
| 4. prijs | ✅ Klaar | Prijsmatrix incl. spoed + maatwerk. 31/31 tests groen. |
| 5. graph_auth | ✅ Klaar | Microsoft-token: public client, refresh-rotatie in token_persist.json, ntfy-noodmelding bij verlopen koppeling. 13/13 tests groen. |
| 6. graph_api | ✅ Klaar | Alle onderdelen af: ✅ agenda, ✅ mail, ✅ onedrive, ✅ todo, ✅ onenote. 51/51 tests groen. |
| 7. agenda_format | ✅ Klaar | Vaste Outlook-opmaak losgekoppeld van de agenda-laag. 17/17 tests groen. |
| 8. events | ✅ Klaar | Centrale append-only logging (fundament dashboard). schrijf_event + lees_events met filters; strikte resultaat-/niveau-waarden; JSONL bovenop storage. 16/16 tests groen. **Hele core nu af: 159/159 tests.** |

**Omgeving:** Claude Code geïnstalleerd op Windows via WSL/Ubuntu. Oude tools staan als leesbron in `OneDrive/1. Werkmap/Claude/Automatiseringstools` (alleen lezen). Geen API-keys in de nieuwe code — alles via env-vars. Oude hardcoded keys (BAG ×2, EP ×1) moeten nog geroteerd worden (zie H8.3).

**Bevinding voor toekomst:** Railway-account 'keviniom' heeft via de GitHub-app Repository access = All repositories ingesteld. Railway kan dus zonder extra configuratie bij alle huidige én toekomstige repos in het Keviniom-account, inclusief private repos zoals energiemeneer-core. Geldt ook voor de geïnstalleerde Anthropic Claude GitHub-app.

**Fundament — fase F1:** ✅ **volledig af** — core compleet (Modules 1–8, 159/159 tests groen).

**Fase 2 (F2) — instroom-tools op de core:** 🔧 **bezig.**
- ✅ **F2.0** — `energiemeneer-core` installeerbaar als Python-package via pip.
- ✅ **F2.2 Stap 1a (plumbing)** — core als dependency + postcode-test, géén gedragsverandering. Bewezen op Railway PR-environment `admin-portal-pr-1`.
- ✅ **F2.2 Stap 1b (postcode-vervanging)** — `normaliseer_postcode` in `server.py` vervangen door `core.bag.normaliseer_postcode`, lokale duplicaat verwijderd. **Gemerged naar main; productie draait nu op de core voor postcode-normalisatie.**
- ✅ **Bonus-fixes meegenomen in dezelfde PR (#1):** domein-typo overal gefixt naar `de-energiemeneer.nl` (met streepje — de admin-notificatie bouncede op het niet-bestaande adres zonder streepje) en tijdformaat-fix (agenda-titel toont nu "13:00 en 14:30 uur" met dubbele punten i.p.v. "1300").
- ⬜ **Volgende: Stap 2** — `bereken_prijs` op de core trekken volgens hetzelfde patroon (eerst plan, dan branch → PR → preview-test → merge).

**Volgende stap:** Stap 2 — in de admin-portal de lokale prijsberekening vervangen door `core.prijs.bereken_prijs` (met een kleine output-adapter voor de bestaande frontend-keys), via dezelfde branch → PR → Railway PR-environment-flow (H10.2/F2.1), pas na groen + functionele check mergen. Losse aandachtspunten blijven: secrets roteren (H8.3) en de aantekeningen voor consolidatie hieronder.

📌 Sinds versie 4.15 bestaat er een levende frictielijst (sectie H6a — Productieve frictie). Bevat 9 punten (1 deels opgelost, 8 open); gebruik als input bij elke prioriteringskeuze.

📌 Sinds versie 4.15 is de schaal-ambitie vastgelegd in sectie H1a — Schaal-horizon (multi-user intern + abonnement voor concullega's). Geen fase, wél input voor architectuur-keuzes (auth, datalaag, hosting, billing).

📌 **Roadmap-volgorde gewijzigd in versie 4.14 (3 juni 2026):** de uitvoeringsvolgorde van F3 t/m F6 is omgegooid. Oude F6 (Intake + Upload als online modules) is opgewaardeerd naar F3, en oude F3 (verhuizing naar eigen hosting) is verschoven naar F6 — pas nadat alle tools draaien en de jobs lopen. Zie H10 voor de volledige tabel en toelichting.

**Aantekeningen voor later (consolidatie):**
- Docker-waarschuwing tijdens Railway-build: secrets via ARG/ENV in Dockerfile/railway.toml (ADMIN_PASSWORD, EP_ONLINE_KEY, MS_CLIENT_SECRET, MS_REFRESH_TOKEN, OVERHEID_API_KEY, SECRET_KEY). Geen build-fout, maar wel best-practice-schuld. Hoort opgeruimd te worden samen met de secret-rotatie van H8.3.
- Mail lézen + bijlagen ophalen (voor Job B/Uploadtool) — bron is `outlook_handler.py`.
- Vaste mapnaam-template "straat huisnr, woonplaats" hoort in een aparte format-module (bijv. `dossier_format`), niet in module 6.
- Foto-resize-logica uit de oude Uploadtool moet een nette plek krijgen (mogelijk `core/foto` of als hulpfunctie in de Upload-module).
- To Do-taken afvinken/bijwerken: losse uitbreiding op graph_api/todo wanneer de dossier-status-tracking aan de beurt is.
- Testknop op `/instellingen` die een admin-notificatie stuurt zónder een afspraak in te plannen — spaart tijd bij elke mail-gerelateerde wijziging. Eigen PR, geen onderdeel van de strangler.
- Productie `/instellingen` controleren: vermoedelijk staan de bedrijfsgegevens daar net zo leeg/fout als op de preview vóór de fix. Bij het eerstvolgende productie-bezoek invullen (email, telefoon, website, KvK, BTW).
- Agenda-titel-opmaak migreren naar `core.agenda_format`: vandaag is in `admin-portal/ms_graph.py` alleen een lokale typo-fix gedaan (`%H%M` → `%H:%M`). De volledige titel-opbouw hoort straks vervangen te worden door `agenda_format.opmaak_opname()` — plan voor een latere strangler-stap, niet nu.

# 0b. Werkwijze — drie rollen, één doel

> Waar H0a vertelt wáár het project staat, vertelt H0b hóé eraan gewerkt
> wordt. Lees beide vooraf: dan weet elke nieuwe chat, elke Claude
> Code-sessie en elke nieuwe collega niet alleen de stand van zaken, maar
> ook wie welke pet op heeft.

Dit platform wordt gebouwd door een driehoek. Geen hiërarchie van baas naar
ondergeschikte, maar drie rollen die elkaar aanvullen en bewaken. Elke rol is
een vangnet voor de volgende: de chat voorkomt dat aan de verkeerde dingen
wordt begonnen, Claude Code voorkomt dat ongeteste of onbesproken code wordt
vastgelegd, en Kevin houdt de eindregie. Wie de prompt typt of in welke
volgorde het loopt, ligt níét rigide vast — de rolverdeling wel.

## De drie rollen

| **Rol** | **Wie/wat** | **Doet** | **Vangnet** |
| --- | --- | --- | --- |
| **Strateeg / gids** | Claude in de chat | Bewaart de strategische context (Meesterbrein-kennis) en het *waarom* achter eerdere keuzes. Stelt plannen op vóór er code is. Formuleert prompts voor Claude Code (Kevin mag dat ook rechtstreeks). Reviewt wat Claude Code rapporteert en biedt alternatieven. | Eerste vangnet — voorkomt dat aan het verkeerde wordt begonnen. |
| **Developer met eigen inzicht** | Claude Code (terminal) | Voert het technische werk uit: lezen, schrijven, testen, committen, pushen. Kent de repo-structuur en de concrete code. Toont diff's vóór akkoord. **Mag en moet eigen, slimmere oplossingen voorstellen** wanneer Kevins of de chat's voorstel niet de beste route is — mits expliciet benoemd wát beter is en waaróm, zodat Kevin bewust kan kiezen. | Tweede vangnet — vraagt akkoord vóór commit/push. |
| **Eigenaar / beslisser** | Kevin | Bepaalt de strategische richting en neemt de eindbeslissingen. Reviewt zowel de plannen van de chat als de uitvoering van Claude Code. Doet de functionele test op de Railway PR-preview en geeft akkoord voor de merge naar productie. | Laatste woord — niets gaat live zonder zijn go. |

De rol "developer met eigen inzicht" is bewust geen "uitvoerder". Claude Code
denkt mee en mag tegenspreken; dat het eigen, betere routes voorstelt is geen
overschrijding maar de bedoeling (zie ook H6a, waar dit principe voor het
oplossen van frictiepunten al staat). Dezelfde rol geldt voor een menselijke
collega-developer (zie ONBOARDING.md).

## Werkstromen — vier varianten, niet rigide

De volgorde hieronder is een richtlijn, geen keurslijf. Kies de lichtste vorm
die bij de taak past.

1. **Grote feature of migratie.** Kevin → plan in de chat → prompt → Claude Code
   → diff + test → akkoord Kevin → commit → preview-test op Railway → merge.
   (Canoniek voorbeeld: F2 Stap 1b, de postcode-vervanging — zie H10.2.)

2. **Vervolgstap binnen lopend werk.** Claude Code rapporteert → Kevin stuurt
   dat door naar de chat → de chat adviseert de vervolgprompt → Kevin plakt die
   → Claude Code voert uit. Een loop die doordraait tot het werk af is.

3. **Kleine bugfix of losse uitvoering.** Kevin gaat direct naar Claude Code,
   zonder tussenstop bij de chat. Claude Code voert uit, Kevin reviewt op de
   PR-preview.

4. **Eigen inzicht van Claude Code.** Ziet Claude Code tijdens het werk iets
   beters, dan benoemt het dat expliciet ("ik stel X voor in plaats van Y,
   omdat …") en wacht op Kevins beslissing. Een triviale verbetering mag het
   meteen meenemen, mits met een heldere melding ("zo geïnterpreteerd: …").

## Niet-onderhandelbaar

- **Geen push naar `main`/`master` zonder akkoord van Kevin** — geldt voor
  Claude Code én voor elke collega.
- **Geen merge naar productie zonder een bewezen functionele test op de
  PR-preview.**
- **Bij twijfel: vraag het. Blokkeer niet, sloop geen werkende code, forceer
  geen merge.** Een open vraag is goedkoper dan een teruggedraaide deploy.
- **Bouw geen deuren dicht** — houd waar het weinig kost rekening met de
  schaal-ambitie (zie H1a Schaal-horizon).

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

# 1a. Schaal-horizon — van één gebruiker naar meerdere

Het platform wordt nu gebouwd voor één gebruiker (Kevin). Op termijn wil De EnergieMeneer twee kanten op kunnen schalen:

- **(a) Intern personeel** — meerdere medewerkers binnen De EnergieMeneer met eigen accounts en een rolverdeling (bijvoorbeeld opname-adviseur, admin, boekhouder), elk met eigen rechten op de modules en de data.

- **(b) Concullega's** — andere energieadvies-bedrijven die via een abonnementsvorm gebruik kunnen maken van (delen van) het platform. Dit maakt het platform op termijn een product op zichzelf, niet alleen een interne tool.

**Deze schaal-ambitie heeft nu geen prioriteit en is géén onmiddellijke fase — F1 t/m F8 (H10) blijven ongewijzigd.** Ze staat hier omdat ze nú al architectuur-keuzes raakt die we maken: het is goedkoper om er rekening mee te houden dan om er later op terug te bouwen. Concreet als input voor het ontwerp:

- **Identity-/auth-laag (H4.3):** moet niet vastroesten als één-Kevin-token, maar zó worden opgezet dat multi-user (meerdere accounts, rollen) er later op past.

- **Datalaag (F4):** moet per-tenant scheiding kunnen ondersteunen — data van verschillende bedrijven strikt gescheiden.

- **Hosting (F6):** moet een multi-tenant deployment aankunnen.

- **Pricing/billing-laag:** wordt te zijner tijd een eigen module (Stripe of vergelijkbaar, met een mogelijke koppeling naar SnelStart en het bestaande F8-spoor).

Kortom: bouw geen deuren dicht. Waar een keuze tussen "single-user simpel" en "multi-user-klaar" weinig extra kost, kiezen we bewust de laatste.

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

- **events** — append-only logboek: elke statuswijziging met tijd, module en resultaat. Voedt het dashboard. *(Gebouwd in core-module 8. Vast event-formaat: `id`, `tijd` (UTC), `module`, `actie`, `resultaat` ∈ {gelukt, mislukt, in_uitvoering}, `niveau` ∈ {info, waarschuwing, kritiek}, `vbo_id`, `bericht`, `details`. `resultaat` en `niveau` zijn strikt — andere waarden geven een fout — zodat het dashboard betrouwbaar kan filteren en kleuren. Opslag nu als JSONL bovenop storage, achter één interne functie zodat B1 (SQLite/PostgreSQL) later in te schuiven is.)*

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

# 6a. Productieve frictie

Dit is een **levend document**. Frictie die herhaaldelijk wordt gevoeld is een signaal dat een fase of module aandacht verdient. Punten met een geschatte tijd-per-week zijn directe input voor prioritering: hoe meer tijd een irritatie structureel kost, hoe zwaarder die meeweegt. De lijst wordt **bijgewerkt zodra een nieuwe irritatie opvalt**, en een punt wordt **geleegd (verwijderd) zodra het structureel is opgelost** door een fase of PR — niet eerder, want een half opgeloste pijn blijft pijn.

**Belangrijk principe bij het oplossen van deze punten:** Claude (zowel in de chat als in Claude Code) mag en moet eigen, slimmere oplossingen voorstellen wanneer Kevins beschrijving wél het probleem dekt, maar niet noodzakelijk de beste oplossing. Kevin is geen doorgewinterde programmeur en kent niet altijd de elegantste route — een goede inval van Claude of de collega is uitdrukkelijk welkom. **Voorwaarde:** benoem expliciet wát je voorstelt en waaróm het beter is dan Kevins oorspronkelijke beschrijving, zodat hij bewust kan kiezen. De beschrijving in de tabel legt de *pijn* vast, niet de verplichte oplossing.

| **#** | **Beschrijving** | **Frequentie** | **Tijd/week** | **Categorie** | **Lost op in fase** | **Status** |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Bij elke energielabel-afmelding moet ik de bijbehorende klant opzoeken aan het adres, de juiste offerte vinden, omzetten naar factuur en de makelaar opzoeken om in de cc te zetten. | bij elk energielabel | ~10 min per keer | Data/integratie | F4 + F8 | Open |
| 2 | De opdrachtbevestiging is dubbelop met de afspraakbevestiging. | bij elke nieuwe aanvraag | nog invullen | Proces/UI | F3 | Open |
| 3 | Agenda-patch toonde tijden als "0900 en 1030 uur" i.p.v. "09:00 – 10:30". Daarnaast: de eerste afspraak van de dag (09:00) verschijnt als puntsafspraak i.p.v. een blokje met eindtijd. | bij elke nieuwe afspraak | — | Bug (klein) | PR #1 (gedeeltelijk) + later in F3 bij agenda_format-migratie | ✅ Tijdformaat (HHMM→HH:MM) is opgelost in PR #1 op admin-portal (gemerged 3 juni 2026). Puntsafspraak-bug voor 09:00: status nog te bevestigen door Kevin (mogelijk ook opgelost — herziening bij volgende functionele test). |
| 4 | De afspraakbevestiging moet meteen dienen als opdrachtbevestiging. Geldt voor zowel klant-self-service (aanmeldformulier) als handmatig inplannen (admin portal). | bij elke nieuwe aanvraag | nog invullen | Proces | F3 (fusie aanmeldformulier + admin-portal) | Open |
| 5 | Bij woning-beoordeling in de admin portal is StreetView soms onvoldoende. Wens: bovenaanzicht (zoals BAG-viewer) toevoegen. | regelmatig | nog invullen | UI-feature | quick fix (PR) | Open — geschikt voor nieuwe collega |
| 6 | Spoed-aanvinkbox bij afspraak inplannen met melding "+ €35 incl. BTW" wanneer mogelijk. Maakt eerste 48 uur zichtbaar in de agenda (standaard nu als bezette ruimte ingebouwd). | gewenst | nog niet meetbaar | Feature | eigen PR | Open — geschikt voor nieuwe collega |
| 7 | Sommige adressen geven foute resultaten in nieuwe-opdracht-aanvragen, bijv. Stille Veerkade 34 vs 34A → dezelfde gegevens. | onbekend (wel reproduceerbaar) | zelden maar wel data-integriteitsrisico | Bug | onderzoek (huisletter-handling in BAG-koppeling) | Open |
| 8 | Inkomende makelaar-aanvraag via aanmeldformulier vergt nu handmatig overkopiëren: gegevens naar admin-portal voor de agenda, daarna SnelStart voor de boekhouding, daarna opdrachtbevestiging + offerte sturen. | nog invullen | nog invullen | Proces/integratie | F3 + F4 + F8 | Open |
| 9 | Makelaar wordt wel benoemd in admin-portal maar komt niet terug in de agenda-patch. | bij elke makelaar-aanvraag | nog invullen | Bug | agenda_format-migratie (F3) | Open |

**Hoe we deze lijst gebruiken**

- Bij elke nieuwe roadmap-sessie controleren of de huidige fase deze pijn adresseert.
- Quick fixes oppakken in losse PR's — niet wachten op grote fases.
- Frictie die níét wordt opgelost door de geplande fases is een signaal om de roadmap te heroverwegen.
- Claude of de collega mag eigen alternatieve oplossingen voorstellen wanneer een betere route mogelijk lijkt; Kevin beslist uiteindelijk.

*De tijd-per-week-kolom is op de meeste punten nog niet ingevuld. Aanvullen zodra meetbaar, zodat prioritering op data gebaseerd kan worden in plaats van op gevoel.*

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

> **Vaste opmaak — één bron in core.agenda_format** Titel: `[Klantnaam]: Energielabel opname [m²]m² tussen [begin] en [eind] uur` (bijv. "Jan Jansen: Energielabel opname 120m² tussen 15:30 en 17:00 uur"; tijden in Amsterdamse tijd, m² vervalt als de oppervlakte onbekend is, naam valt terug op "Klant onbekend"). Locatie: volledig adres. Duur: 90 minuten. Reminder: 60 min van tevoren. Body: klantnaam, e-mail, telefoon, adres, bouwjaar, oppervlakte, huidig label, woningtype, prijs, makelaar (indien ingevuld), zakelijke gegevens (indien van toepassing), opmerkingen — alle klantinvoer HTML-veilig. Geldt identiek voor alle instroomkanalen — Kevin ziet in zijn agenda altijd hetzelfde overzicht. *(Beslissing 1 juni 2026: titel bewust de bewezen oude-stijl met klantnaam + m² + tijden, i.p.v. de eerdere adres-variant — geeft in de agenda in één oogopslag wie/hoe laat.)*

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

> **Toelichting volgordewijziging (versie 4.14, 3 juni 2026):** verhuizing naar eigen hosting (oude F3) is verschoven naar het einde omdat het een infrastructuur-verandering is zonder directe productiviteitswinst. Eerst alle tools op de core (oude F6, nu F3), dan de datalaag en jobs draaiend krijgen — dat levert de échte tijdwinst voor het hoofddoel. Verhuizing kan daarna in alle rust.

| **Fase** | **Wat** | **Waarom hier** | **Status** |
| --- | --- | --- | --- |
| F0 | Secrets opschonen + repo’s taggen | Veiligheid; natuurlijk moment vóór verhuizing | Direct |
| F1 | energiemeneer-core extraheren (storage, auth, graph, bag, ep, prijs, agenda) | Fundament; maakt al het andere goedkoper; lost K2+K4 op | ✅ Klaar (Modules 1–8, 159/159 tests) |
| F2 | Fusie Aanmeldformulier + Admin Portal op de core | Één instroom-backend, één login, één token; lost K3 deels op | 🔧 Mee bezig (F2.0 klaar, zie H10.2) |
| F3 | Intake + Upload als online modules op de core | Tools op de core; directe productiviteitswinst voor het hoofddoel | Na F2 |
| F4 | Centrale datalaag + dashboard (status/logs/fouten) | Overzicht over alles; lost K1+K3 volledig op | Na F3 |
| F5 | Job A + Job B online aansturen vanuit platform | De grote tijdwinst, nu op schoon fundament | Na F4 |
| F6 | Verhuizing naar eigen hosting + portal-schil | Infrastructuur-stap zónder directe productiviteitswinst; kan ná alle tools/jobs | Na F5 |
| F7 | VvE-module met web-UI + advies-trajecten | Verbreding naar VvE/advies; volgende omzetstroom | Later |
| F8 | SnelStart-koppeling (Make.com) + EP-Online API v5 | Facturatie- en label-status-automatisering | Te verkennen |

## 10.1 Wat dit oplevert voor het hoofddoel

De tijdwinst zit niet in één moment, maar in alles wat erna goedkoper wordt. Een wijziging die nu 3–5× moet, hoeft straks één keer. Job A bouwen op een schoon fundament is sneller en minder bug-gevoelig dan op vijf eilanden. Het platform maakt elke volgende uitbreiding (VvE, advies) een module in plaats van een nieuw eiland — zo blijft de automatisering productietijd vrijspelen richting het hoofddoel.

## 10.2 F2 — voortgang in onderdelen

**F2.0 Installeerbaar maken (1 juni 2026):** pyproject.toml in de core gevuld met tzdata-dependency (msal niet nodig — graph_auth regelt tokens zelf via requests). Setuptools als builder. Schone-venv-test geslaagd: pip install . in verse venv, alle imports werken, tzdata bewijst Amsterdamse tijdzone-conversie (UTC 13:30 → AMS 15:30 +zomertijd), geen testbestanden in site-packages.

**Stap 1a — plumbing bewezen op Railway (1 juni 2026):** de admin-portal neemt `energiemeneer-core` als dependency op (via publieke GitHub-tag, anoniem bereikbaar zonder credentials). PR-environment `admin-portal-pr-1`: Nixpacks-build slaagde, `energiemeneer-core 0.1.0` schoon geïnstalleerd, healthcheck groen, `/healthz`-endpoint geverifieerd in de browser ("ok"-response). Hiermee is de leidingenloop bewezen vóór er functionaliteit verschoof. Volgende: stap 1b — postcode-vervanging in `server.py`.

### F2.1 — Railway PR Previews als veiligheidsmechanisme

Voor alle services binnen project helpful-manifestation (admin-portal, en straks ook andere) is in Railway PR Environments aangezet (Project Settings → Environments → 'Enable PR Environments'). Base environment: 'No base environment' (Railway pakt automatisch production-variabelen). Focused PR Environments is UITGEZET na eerste test (zie ontdekking hieronder).

Werkwijze voor élke strangler-stap vanaf nu:
1. Branch maken in Claude Code, pushen naar GitHub
2. Pull Request openen op GitHub (base: main, compare: feature-branch)
3. Railway maakt automatisch PR-environment aan (admin-portal-pr-N)
4. Build + healthcheck draaien in PR-environment — productie wordt niet aangeraakt
5. Pas na groen vinkje + functionele check op de preview-URL: PR mergen naar main → Railway deployt naar productie
6. PR sluiten → Railway ruimt PR-environment automatisch op

Ontdekking: 'Focused PR Environments' (credit-besparende feature die alleen geraakte services deployt) markeerde de admin-portal-service bij PR #1 als 'Not affected by PR' terwijl er wel relevante wijzigingen waren (requirements.txt, tests/, CLAUDE.md). Work-around: handmatig op 'Deploy' klikken op de service-card binnen de PR-environment. Definitieve oplossing: Focused PR Environments UITgezet (geen verspilling want momenteel maar 1 service per project). Bij meerdere services later: heroverwegen of Watch Paths (*.py, requirements.txt, railway.toml) een betere route is.

### F2.2 — Strangler-discipline (geleerde patronen)

De eerste functie in de admin-portal is vervangen door een core-aanroep (postcode-normalisatie, stap 1a/1b — 1 juni 2026, gemerged naar main). Tijdens stap 1b zijn de volgende werkpatronen bevestigd of ontdekt — bewaar als richtlijn voor toekomstige strangler-stappen.

1. **Splits 1a/1b per stap:** plumbing eerst (dependencies + tests, géén gedragsverandering, branch + PR + preview-build), daarna pas gedragsverandering (de eigenlijke vervanging). Niet mengen in dezelfde commit-historie.

2. **'Bevroren ijkpunt'-test:** in de admin-portal-test staat een kopie van de oude lokale logica ingebakken. Ook nadat de echte lokale code uit `server.py` is, blijft de test bewaken dat de core hetzelfde doet als wat de portal vroeger deed. Dit patroon hergebruiken voor toekomstige migraties.

3. **Hardcoded vs persistent instellingen:** bedrijfsspecifieke data (email, telefoon, KvK) hoort in `/instellingen` (persistent op disk), niet in code-defaults. Code-defaults blijven leeg óf bevatten alleen veilige fallback-waarden. Na merge: productie `/instellingen` apart controleren — staat vermoedelijk hetzelfde als wat de preview toonde vóór de fix.

4. **Bonus-fixes mogen mee in een strangler-PR** — mits ze klein en geïsoleerd zijn (één regel, één concept). Grotere vondsten krijgen een eigen PR. Bij twijfel: splitsen voor een schone historie.

5. **Mergen vanuit Claude Code** (`git merge --no-ff` + push naar main, eventueel met `gh` CLI om de PR netjes te sluiten) werkt prima — bespaart browsertabs. Discipline blijft: mergen pas na Kevins expliciete akkoord na preview-test.

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
| 4.9 | 1 juni 2026 | Module 7 (agenda_format) klaar en getest (17/17) — **daarmee is de hele core (Modules 1–7) af: 143/143 tests groen.** Vaste Outlook-opmaak losgekoppeld van de generieke agenda-laag: pure functie opmaak_opname levert titel + HTML-body + locatie + herinnering; agenda weet *hoe*, agenda_format weet *wat*. Klantinvoer wordt HTML-veilig gemaakt. H9.3-titel gelijkgetrokken met de gekozen oude-stijl (klantnaam + m² + Amsterdamse tijden) i.p.v. de eerdere adres-variant. Fundament-fase F1 afgerond; volgende fase is F2 (instroom-tools op de core trekken). |
| 4.10 | 1 juni 2026 | Module 8 (events) toegevoegd aan de core en getest (16/16) — totaal 159/159. Centrale append-only logging als fundament voor het dashboard (H6): schrijf_event + lees_events (filters op module/vbo_id/resultaat/niveau/sinds/limiet, nieuwste eerst), bovenop storage als JSONL. Vast event-formaat vastgelegd in H4.2; resultaat (gelukt/mislukt/in_uitvoering) en niveau (info/waarschuwing/kritiek) zijn strikt — geen vrije tekst — zodat het dashboard betrouwbaar kan filteren/kleuren. Opslag achter één interne functie, zodat beslispunt B1 (echte DB) later in te schuiven is. |
| 4.11 | 1 juni 2026 | F2.0 afgerond — energiemeneer-core is nu installeerbaar als Python-package via pip (energiemeneer-core @ git+...). pyproject.toml uitgebreid met tzdata-dependency. Schone-venv-test bewees correcte installatie inclusief Amsterdamse tijdzone-conversie. Bevinding vastgelegd: Railway-GitHub-app heeft 'All repositories'-toegang op het Keviniom-account, dus geen extra configuratie nodig voor F2.1. Volgende: F2.2 — eerste functie in admin-portal door core-aanroep vervangen (strangler-aanpak). |
| 4.12 | 1 juni 2026 | F2 gestart en eerste plumbing-stap (1a) bewezen op Railway. PR Environments aangezet in Railway Project Settings voor automatische preview-deployments per Pull Request. Branch core-integratie-stap1a → PR #1 op admin-portal-repo → PR-environment admin-portal-pr-1: Nixpacks-build slaagde, energiemeneer-core 0.1.0 schoon geïnstalleerd vanaf publieke GitHub-tag (anoniem bereikbaar zonder credentials), healthcheck groen, /healthz endpoint geverifieerd in browser. Werkwijze voor alle toekomstige strangler-stappen vastgelegd in nieuwe sectie F2.1. Ontdekking: 'Focused PR Environments' markeerde service als niet-geraakt (work-around: handmatige Deploy; definitief opgelost door Focused uit te zetten — werkt prima met 1 service per project). Aantekening toegevoegd: Docker-warning over secrets in ARG/ENV hoort bij secret-rotatie H8.3. Volgende: stap 1b — postcode-vervanging in server.py, opnieuw via PR-flow. |
| 4.13 | 1 juni 2026 | F2 Stap 1b (postcode-vervanging) gemerged naar main — admin-portal draait nu in productie op core.bag.normaliseer_postcode. Bonus-oogst meegenomen in dezelfde PR: (a) domein-typo overal gefixt naar de-energiemeneer.nl met streepje (instellingen.py, email_templates.py, klant_portaal.html), (b) agenda-titel toont nu netjes 'HH:MM en HH:MM uur' met dubbele punten in plaats van 'HHMM en HHMM uur'. Nieuwe sectie F2.2 toegevoegd met geleerde patronen (1a/1b-splitsing, bevroren ijkpunt-test, hardcoded vs persistent instellingen, bonus-fix-regel, merge-vanuit-Claude-Code). Aandachtspunten toegevoegd: testknop bouwen, productie-instellingen checken, agenda-format-migratie als latere strangler-stap. Volgende: F2 Stap 2 — bereken_prijs op de core trekken volgens hetzelfde patroon. |
| 4.14 | 3 juni 2026 | Strategische roadmap-wijziging — uitvoeringsvolgorde van F3-F6 omgegooid op verzoek van Kevin. Intake + Upload online modules (was F6) opgewaardeerd naar F3 omdat het directe productiviteitswinst levert. Verhuizing naar eigen hosting (was F3) verschoven naar F6 — pas nadat alle tools draaien en jobs lopen. Hernummering: oude F3↔F6 omgewisseld; F4, F5, F7, F8 ongewijzigd. Alle interne kruisverwijzingen in het document gelijkgetrokken. Korte toelichting boven H10-tabel toegevoegd. |
| 4.15 | 3 juni 2026 | **Twee toevoegingen.** (1) Nieuwe sectie H6a — Productieve frictie: levende lijst van 9 dagelijkse irritaties uit Kevin's werk, gecategoriseerd (bug / proces / UI-feature / data-integratie) en gekoppeld aan welke fase ze structureel oplost. Twee punten (bovenaanzicht in admin-portal, spoedbox bij afspraak) gemarkeerd als geschikt voor de nieuwe collega. Tijdformaat-bug (HHMM→HH:MM) uit PR #1 erkend als opgelost; puntsafspraak-bug voor 09:00 nog te bevestigen. Belangrijk toegevoegd principe: Claude en collega mogen eigen slimmere oplossingen voorstellen bij het oplossen van punten — Kevin's beschrijving dekt het probleem, niet noodzakelijk de beste oplossing. (2) Nieuwe sectie H1a — Schaal-horizon: schaal-ambitie vastgelegd (multi-user voor intern personeel met rollen, en abonnementsvorm voor concullega's). Expliciet géén fase en geen wijziging aan F1–F8, maar input voor architectuur-keuzes die nu al spelen: multi-user auth-laag, per-tenant datalaag (F4), multi-tenant hosting (F6) en een toekomstige pricing/billing-module (Stripe, mogelijke SnelStart-koppeling). |

| 4.16 | 3 juni 2026 | **Werkwijze expliciet vastgelegd in drie bestanden.** Nieuwe sectie H0b — Werkwijze (drie rollen, één doel): de samenwerkingsdriehoek tussen Claude in de chat (strateeg/gids), Claude Code (developer met eigen inzicht) en Kevin (eigenaar/beslisser), met een rollentabel, vier niet-rigide werkstromen en de niet-onderhandelbare regels (geen push naar main zonder akkoord, geen merge zonder bewezen preview-test, bij twijfel vragen, geen deuren dichtbouwen). CLAUDE.md uitgebreid met "Jouw rol als Claude Code" (developer met eigen inzicht, mag/moet slimmere oplossingen voorstellen, strategie via Kevin). ONBOARDING.md §3 uitgebreid met de driehoek en de plek van de nieuwe collega (óók developer met eigen inzicht). Kruisverwijzingen naar H6a (eigen-inzicht-principe) en H1a (bouw geen deuren dicht) i.p.v. duplicatie. |

*— Einde document —*
