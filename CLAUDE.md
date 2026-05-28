# CLAUDE.md — vaste instructies voor Claude Code

> Claude Code leest dit bestand automatisch bij elke start. Hier staan de
> afspraken die altijd gelden, zodat Kevin ze niet elke sessie opnieuw hoeft
> te typen.

## Wie is de gebruiker

Kevin Valkenhoff — eigenaar van De EnergieMeneer (energielabels, VvE- en
energieadvies). **Geen doorgewinterde programmeur.** Leg dingen in gewone taal
uit, vermijd jargon, en wees een geduldige gids. Communiceer in het Nederlands,
informeel maar professioneel.

## Wat dit project is

`energiemeneer-core` — een gedeelde Python-library die de herhaalde logica uit
Kevins vijf losse tools bundelt op één plek. Onderdeel van een groter plan
(het platform) dat volledig beschreven staat in `Meesterbrein.md`.

## ⚠️ ALTIJD EERST DOEN bij een nieuwe sessie

1. Lees `Meesterbrein.md` (vooral H0a Bouwstatus — daar staat waar we zijn).
2. Lees `BOUWPLAN.md` (de volgorde en werkwijze van de modules).
Dan weet je de context en hoef je niets te vragen wat daar al in staat.

## Gouden regels bij het bouwen

- **Strangler-aanpak:** hergebruik de schoonste bestaande versie uit Kevins
  oude tools (staan als leesbron in
  `/mnt/c/Users/kevin/OneDrive - De Energiemeneer/1. Werkmap/Claude/Automatiseringstools`).
  Verzin niets vanaf nul als er bewezen code is. NOOIT een werkende kopie
  slopen voordat de vervanging bewezen werkt.
- **Leg eerst je plan uit in gewone taal, schrijf nog GEEN code, en wacht op
  Kevins akkoord.** Dit is de belangrijkste regel. Geen verrassingen.
- **Eén module tegelijk.** Bouw, test, vink af in BOUWPLAN.md, commit. Stop op
  een groen punt — niet doorrazen naar de volgende module zonder akkoord.
- **Geef na elke module een korte samenvatting in gewone taal** van wat er nu
  werkt (geen technische dump).

## Codeconventies (vastgelegd in modules 1–4)

- Nederlandse functienamen (bijv. `vind_data_dir`, `zoek_adres`, `bereken_prijs`).
- Logging via `logging.getLogger("energiemeneer_core.<module>")` — NOOIT `print`.
- Nette, begrijpelijke foutmeldingen (Nederlands).
- **NOOIT hardcoded API-keys of secrets overnemen** uit de oude tools. Alles
  strikt via environment variables. Ontbreekt een key → nette RuntimeError met
  uitleg welke env-var gezet moet worden.
- Atomic writes voor bestanden (tmp + os.replace), met lock waar nodig.
- Tests met pytest, externe calls mocken (geen echte HTTP in tests).

## ⚠️ Versiebeheer van Meesterbrein.md

Het bestand heet **altijd** `Meesterbrein.md` — **NOOIT hernoemen** naar een
genummerde variant. Het versienummer leeft alleen in de tabel bovenin het
document. Bij een wijziging: hoog dat nummer op en voeg een regel toe aan de
versiehistorie. Lever altijd terug onder dezelfde naam.

## Git

- Commit na elke afgeronde, geteste module met een duidelijke NL-boodschap.
- `git push` (naar GitHub) is een bewuste stap — meld het even voordat je pusht
  de eerste keer in een sessie.
- Git-gebruiker is al globaal ingesteld (Kevin Valkenhoff / kevinvalkenhoff@gmail.com).

## Wat NIET te doen

- Geen nieuwe modules of features beginnen die niet in BOUWPLAN.md staan zonder
  het eerst met Kevin te overleggen.
- Niet Kevins oude tools wijzigen tijdens het bouwen van de core — die zijn
  alleen leesbron. (Het aanpassen van oude tools is een latere, aparte fase.)
- Niet doorrazen door meerdere beslissingen heen — Kevin houdt de regie.
