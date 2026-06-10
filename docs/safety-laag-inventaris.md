# Safety-/policy-laag — inventaris & plan van aanpak

> Status: **fake-client-modus + eerste twee remmen aangehaakt** (juni 2026).
> `environment.py` is niet langer inert: `storage`, `graph_auth`, de
> `graph_api`-modules, `bag` en `ep_online` raadplegen 'm nu. Dit document
> blijft de bron voor wélke schrijfpunten er zijn, welke rem erbij hoort, en
> wat er nog moet gebeuren (vooral in admin-portal). Bron: onderzoek 10 juni
> 2026, bijgewerkt na de fake-clients-bouw.

## Wat nu gebouwd is (in core)

- **`use_fake_clients()`** — non-prod = fake, prod = echt; override via
  `USE_FAKE_CLIENTS`. Zichtbaar in `describe()`/`banner()` (`clients: FAKE/echt`).
- **Fake Microsoft Graph-client** (`graph_api/_fake_client.py`) achter één swap
  in `_client.verzoek()`; auth gestubd in `graph_auth` (token + device-login);
  OneDrive >4 MB-carve-out; **stateful OneNote** zodat `kopieer_sjabloonpagina`
  end-to-end draait. Dev/test heeft géén Microsoft 365-connectie meer nodig.
- **Fakes voor de externe core-reads:** `bag.zoek_adres`/`vrij_zoeken` en
  `ep_online.zoek_op_vbo`/`zoek_op_adres` geven in fake-modus realistische
  fixtures, zonder API-key of netwerk.
- **`mail_enabled()`** aangehaakt in `stuur_mail` (rem #1).
- **`storage_root()`** gereconcilieerd met `vind_data_dir()` (rem #7–9): override
  → anders de bestaande autodetectie. Zie aandachtspunt A (opgelost: wrappen).

Tests draaien standaard op het **echte** pad (`tests/conftest.py` zet
`USE_FAKE_CLIENTS=0`); fake-tests zetten zelf `=1`. Volledige suite groen.

## Kernbevinding (lees dit eerst)

De policy-laag (`environment.py`) leeft in **core**, maar de twee zwaarste
remmen die hij beschrijft horen bij code die **niet in deze repo staat**:

- **De 06:00-scheduler / "Job A"** zit volledig in **admin-portal**
  (`job_voorbereiden.py`, endpoint `/api/job-a/run`). In de hele core-repo
  staat geen enkele `schedule`/`cron`/`Timer`/`while True`-loop die een
  dagelijkse job start.
- **De EP-Online-upload naar de koepel** bestaat in core alleen als
  *opzoeken* (read-only GET in `ep_online.py`). De echte upload-naar-de-koepel
  is volgens Meesterbrein H7.3 "upload-module increment 2 — nog niets voor
  gebouwd"; increment 1 zit in **admin-portal** (`upload.py`).

Gevolg: **`uploads_enabled()` en `scheduler_enabled()` hebben in deze repo geen
schrijfpunt om achter te hangen.** Die guards horen in admin-portal en zijn een
aparte stap, ná een werkende test.

## Inventaris van alle schrijfpunten naar buiten (in core)

| # | Side-effect | Bestand / functie | Soort | Welke rem hoort erbij |
|---|---|---|---|---|
| 1 | Mail versturen | `graph_api/mail.py` → `stuur_mail` → `_client.post("/me/sendMail")` | Graph write | **`mail_enabled()`** — kan hier |
| 2 | Noodmelding push | `graph_auth.py:342` → `_waarschuw_opnieuw_inloggen` → `requests.post(ntfy.sh)` | externe push | grijs gebied — zie hieronder |
| 3 | Agenda aanmaken/wijzigen/annuleren | `graph_api/agenda.py` → `maak_afspraak` / `wijzig_afspraak` / `annuleer_afspraak` (post/patch/delete `/me/events`) | Graph write | géén vlag in env-laag |
| 4 | OneDrive map + bestand | `graph_api/onedrive.py` → `maak_map`, `upload_bestand` (+ `_upload_klein/_groot`, `requests.put`-sessie) | Graph write | géén vlag in env-laag |
| 5 | OneNote pagina kopiëren/vullen | `graph_api/onenote.py:178/244` (post/patch) | Graph write | géén vlag in env-laag |
| 6 | To Do taak/lijst aanmaken | `graph_api/todo.py:60/165` (post) | Graph write | géén vlag in env-laag |
| 7 | Lokale JSON-write | `storage.py` → `bewaar_json` (atomic tmp+replace) | lokale file | **`storage_root()`** — chokepoint |
| 8 | Events-logboek (append) | `events.py` → `schrijf_event` (`open(pad,"a")` via `storage.pad_voor`) | lokale file | **`storage_root()`** (via storage) |
| 9 | Refresh-token opslaan | `graph_auth.py` → `_bewaar_refresh_token` (via `storage.bewaar_json`) | lokale file | **`storage_root()`** (via storage) |
| — | OAuth token-posts | `graph_auth.py:144/186/241` | login, géén side-effect | géén rem nodig |

**Observatie:** alle lokale writes (7, 8, 9) lopen al via één chokepoint:
`storage.vind_data_dir()`. Wie dáár `storage_root()` inhangt, dekt drie
schrijfpunten in één klap. Dat is de schone reconciliatie-plek.

## Schrijfpunten & externe reads die NIET in deze repo zitten

Deze horen bij de **admin-portal-fase** (ná de core-release met de fakes), niet
bij deze core-push:

| Onderdeel | Waar het wél leeft | Bijbehorende stap |
|---|---|---|
| 06:00-scheduler / "Job A" | admin-portal (`job_voorbereiden.py`, `/api/job-a/run`) | `scheduler_enabled()` — check **vóór** de cron/thread-registratie |
| EP-Online-upload naar koepel | admin-portal (`upload.py`) | `uploads_enabled()` — **zie hieronder: kan nu nog niet** |
| Banner-preflight bij opstart | admin-portal (de app-entrypoint; core is een library) | `banner()` aanroepen bij startup |
| **3DBAG-gebouwhoogte (read)** | admin-portal (`voorbereiden.py`, geport uit `data_api.py`) | fake in de admin-portal-fase |
| **Overpass / OSM (read)** | admin-portal (voorgevel-oriëntatie e.d.) | fake in de admin-portal-fase |

### `uploads_enabled()` kan nu nog niet aangehaakt worden

De vlag bestaat in `environment.py`, maar de **upload-naar-de-koepel zelf is nog
niet gebouwd**: dat is upload-module *increment 2* (extern EnergielabelPortaal/
koepel + 2FA-uit-mail + portaal-credential + headless browser), volgens
Meesterbrein H7.3 "nog niets voor gebouwd". Er is dus geen schrijfpunt om de
guard achter te hangen. Aanhaken zodra increment 2 in admin-portal bestaat —
guard rond de daadwerkelijke koepel-upload.

### 3DBAG- en Overpass-reads horen in admin-portal, niet in core

De fakes in deze core-push dekken alleen de externe reads die **in core** leven
(BAG/PDOK en EP-Online). De **3DBAG-gebouwhoogte** en de **Overpass/OSM**-reads
zitten in de admin-portal (`voorbereiden.py`), niet in deze repo. Ze faken hoort
daarom thuis in de admin-portal-fase, ná deze core-release — zelfde aanpak als
de BAG/EP-fakes (guard op publiek-functie-niveau achter `use_fake_clients()`).

## Twee aandachtspunten (beide afgehandeld)

**A. `storage_root()` botste met hoe core de root vindt — ✅ opgelost door
wrappen.** Gekozen: `storage_root()` wrapt de bestaande autodetectie. Concreet
leest `environment.storage_root_override()` alleen de env (`STORAGE_ROOT` →
non-prod `STORAGE_ROOT_TEST` → `None`), en `storage.vind_data_dir()` raadpleegt
die override eerst; is hij `None`, dan draait de **bewezen Railway-volume-
autodetectie ongewijzigd** door. Eenrichtingsimport storage → environment, geen
circulaire import. De oude strikte `RuntimeError`-variant is verwijderd.

**B. Geen vlag voor #3–6; ntfy is een uitzondering — ✅ afgehandeld.**
Agenda/OneDrive/OneNote/ToDo krijgen (bewust) géén eigen vlag: in dev/test
worden ze nu door de **fake Graph-client** afgevangen, wat de dev-veiligheid
dekt; in prod horen ze gewoon te werken. De ntfy-noodmelding (#2) is vrijgelaten
— die loopt buiten de client om en vuurt in fake-modus toch niet (de auth faalt
niet meer), dus het alarm blijft in test stil zonder het te smoren.

## Plan van aanpak — stand van zaken

Gebouwd in deze core-push (één component per commit):

1. ✅ **Mail (#1):** `mail_enabled()`-check vóór de `post` in `stuur_mail` →
   logregel + `return False` bij "uit".
2. ✅ **Storage (#7,8,9):** `storage_root()` gereconcilieerd met
   `vind_data_dir()` (wrappen, niet ernaast).
3. ✅ **Fake-client-modus:** `use_fake_clients()` + fake Graph-client (incl.
   stateful OneNote) + fakes voor BAG/EP-Online.

Nog te doen (admin-portal-fase, ná de core-release):

4. **Banner-preflight:** de daadwerkelijke `banner()`-aanroep bij opstart hoort
   in admin-portal (core is een library).
5. **Scheduler:** `scheduler_enabled()` als check vóór de cron/thread-registratie.
6. **EP-Online-upload (increment 2):** `uploads_enabled()` rond de koepel-upload
   — pas mogelijk zodra increment 2 bestaat (zie hierboven).
7. **3DBAG- en Overpass-reads faken** in admin-portal (zie hierboven).

## Wél bewerkt in deze core-push

Naast de inerte eerste commit (alleen `environment.py` toegevoegd) zijn in de
vervolgcommits **bestaande modules bewerkt** om de fakes/remmen achter
`use_fake_clients()` (en `mail_enabled()`/`storage_root()`) aan te haken:
`storage.py`, `graph_api/mail.py`, `graph_api/_client.py`, `graph_auth.py`,
`graph_api/onedrive.py`, `bag.py` en `ep_online.py` (plus de nieuwe
`graph_api/_fake_client.py` en `tests/conftest.py`). "Alleen `environment.py`
toegevoegd" gold dus enkel voor die eerste, inerte commit.

## Bewust niet aangeraakt

- Geen versie-tag, geen pin in admin-portal — dat doen we apart, na een
  werkende test.
- Geen admin-portal-edits in deze core-push.
