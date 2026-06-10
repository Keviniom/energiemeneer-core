# Safety-/policy-laag — inventaris & plan van aanpak

> Status: **onderzoek afgerond, nog niets aangehaakt.** `environment.py` is
> bewust **inert** gecommit (geen enkele module importeert hem nog). Dit
> document legt vast wélke schrijfpunten er zijn, welke rem erbij hoort, en
> wat er nog moet gebeuren — zodat we later zonder opnieuw uitzoeken kunnen
> aanhaken. Bron: onderzoek 10 juni 2026.

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

## Schrijfpunten die NIET in deze repo zitten

| Side-effect | Waar het wél leeft | Bijbehorende rem |
|---|---|---|
| 06:00-scheduler / "Job A" | admin-portal (`job_voorbereiden.py`, `/api/job-a/run`) | `scheduler_enabled()` — check **vóór** de cron/thread-registratie |
| EP-Online-upload naar koepel | admin-portal (`upload.py`, increment 2 nog niet gebouwd) | `uploads_enabled()` |
| Banner-preflight bij opstart | admin-portal (de app-entrypoint; core is een library) | `banner()` aanroepen bij startup |

## Twee aandachtspunten

**A. `storage_root()` botst met hoe core de root nu vindt — risico voor
productie.** `vind_data_dir()` (huidig) detecteert eerst automatisch het
Railway-volume (`/app/data` enz.), dan `ENERGIEMENEER_DATA_DIR`, dan cwd.
`storage_root()` (nieuw) eist in prod een `STORAGE_ROOT` env-var en gooit een
fout als die ontbreekt. `vind_data_dir` botweg vervangen door `storage_root`
**verliest de Railway-volume-autodetectie** die admin-portal in productie nu
gebruikt → dat breekt live. Voorstel: `storage_root()` **wrappen om**
`vind_data_dir()` heen (env-var wint als gezet, anders volume-autodetectie als
basis), zodat de remlogica leidend wordt zónder de bewezen autodetectie te
slopen. Te beslissen: wrappen vs. vervangen.

**B. Geen vlag voor #3–6, en de ntfy-noodmelding is een uitzondering.**
Agenda/OneDrive/OneNote/ToDo zijn echte Graph-writes maar vallen onder geen
enkele bestaande vlag. Te beslissen: ongemoeid laten (alleen mail + storage
remmen) of een aparte vlag/keuze toevoegen. De ntfy-noodmelding (#2) is juist
bedoeld om te werken als alles stuk is — die achter `mail_enabled()` zetten zou
het alarm in test laten zwijgen; voorstel is 'm vrij te laten.

## Plan van aanpak (na akkoord, in losse stappen)

1. **Mail (#1):** `mail_enabled()`-check vóór de `post` in `stuur_mail`. Bij
   "uit": duidelijke logregel (`MAIL_ENABLED uit — mail aan X overgeslagen`) en
   netjes `return False` i.p.v. stil niets doen.
2. **Storage (#7,8,9):** `storage_root()` reconciliëren met `vind_data_dir()`
   (wrappen, niet ernaast), zodat alle lokale writes automatisch de juiste
   bestemming volgen.
3. **Banner-preflight:** klaarzetten/documenteren; de daadwerkelijke aanroep
   bij opstart hoort in admin-portal (core is een library).
4. **Scheduler + EP-upload:** **niet in deze repo** — aparte stap in
   admin-portal, ná een werkende test. `scheduler_enabled()` als check vóór de
   cron/thread-registratie; `uploads_enabled()` rond de koepel-upload.

## Bewust niet aangeraakt

- Geen edits aan bestaande modules (alleen `environment.py` is toegevoegd).
- Geen versie-tag, geen pin in admin-portal — dat doen we apart, na een
  werkende test.
