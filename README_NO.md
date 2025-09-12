# 🔥 CyberSentinel AI - Automatisert sikkerheetsovervåking og AI-analysesystem

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

CyberSentinel AI er et **automatisert sikkerheetsovervåkings- og AI-analysesystem** designet for å **spore de nyeste sikkerhetssårbarhetene (CVE-er)** og **sikkerhetsrelaterte repositories på GitHub** i sanntid. Det utnytter **kunstig intelligens (AI)-teknologi** for dyptgående analyse og **publiserer automatisk verdifull sikkerhetsinformasjon til en bloggplattform**.

## 🚀 Hovedfunksjoner

*   **Overvåking av flere datakilder**:
    *   **CVE-overvåking**: Sanntidsscraping av den nyeste CVE-relaterte informasjonen fra GitHub, som muliggjør rask oppdagelse og sporing av de nyeste sårbarhetstrendene.
    *   **GitHub Repository-overvåking**: Omfattende overvåking av sikkerhetsrelaterte åpen kildekode-prosjekter på GitHub gjennom nøkkelordsøk og forhåndsdefinerte overvåkingslister.
*   **Intelligent AI-analyse**:
    *   **OpenAI & Gemini dobbeltmotor**: Integrert med OpenAI og Gemini AI-modeller, som gir kraftige naturlige språkbehandlingskapasiteter for dyptgående sikkerhetsdataanalyse.
    *   **Flerdimensjonal sikkerhetsvurdering**: Evaluering av CVE-er og repositories fra flere dimensjoner, inkludert **sårbarhetsprinsipper**, **utnyttelsesmetoder**, **risikonivåer** og **påvirkningsomfang**, som sikrer dybde og bredde i analysen.
    *   **Verdivurdering og filtrering**: Intelligent AI-drevet vurdering av sikkerhetsinformasjonens verdi, automatisk filtrering av lavverdige informasjon og fokus på virkelig bemerkelsesverdige sikkerhetstrusler og teknologier.
*   **Automatisert arbeidsflyt**:
    *   **Fullstendig automatisert overvåking**: Systemet kjører **24/7** uten tilsyn, automatiserer sikkerhetsinformasjonsinnsamling, analyse og rapportgenerering.
    *   **Daglig sikkerhetsbriefing**: Genererer daglige sikkerhetsbriefingrapporter på en tidsplan, oppsummerer de nyeste CVE-sårbarhetene og GitHub-sikkerheetsrepositorydynamikk, og sender dem til en bloggplattform.
    *   **Dynamisk svartelisting**: Oppdaterer automatisk svartelister basert på AI-analyseresultater, reduserer interferens fra ugyldig informasjon og forbedrer overvåkingseffektiviteten.
*   **Fleksibel konfigurasjon og administrasjon**:
    *   **Multi-GitHub Token-støtte**: Støtter konfigurasjon av flere GitHub-tokens, intelligent rotasjon av bruk for å effektivt unngå API-hastighetsbegrensninger.
    *   **Konfigurerbare overvåkingsparametere**: Nøkkelord, overvåkingsrepositorylister, svartelister osv. kan fleksibelt justeres gjennom konfigurasjonsfiler for å møte ulike overvåkingsbehov.
    *   **Detaljert logging**: Detaljerte logger registreres for alle kritiske trinn i systemoperasjoner, noe som letter feilsøking og systemovervåking.
*   **Automatisert bloggpublisering**:
    *   **Integrert bloggplattform**: Integrert med en bloggplattform-API for å automatisk publisere daglige sikkerhetsbriefingrapporter, raskt dele sikkerhetsinformasjon.
    *   **Markdown-rapporter**: Analyseresultater og sikkerhetsbriefinger genereres i **Markdown-format**, noe som gjør dem enkle å lese og redigere.

## 🛠️ Teknisk implementering

### 1. Overvåkingsmoduler (Monitors)

*   **`cve_monitor.py`**: **CVE-monitor**
    *   **GitHub API-interaksjon**: Bruker GitHub API til å søke etter CVE-relaterte repositories, nøkkelord `CVE-202+`, og sorterer etter `updated` tid.
    *   **CVE-informasjonsutvinning**: Trekker ut CVE-numre fra repositorynavn og beskrivelser ved hjelp av regulære uttrykk.
    *   **Repository-informasjonscrawling**: Henter repositorybeskrivelser, stjerneskårer, oppdateringstider, nylige commits og annen informasjon.
    *   **Svartelistefiltrering**: Støtter **brukersvartelister** og **repositorysvartelister** for å filtrere ut ugyldige informasjonskilder.
    *   **Filinnholdsanalyse**: Kloner repositories lokalt og **intelligent analyserer** **README.md** og andre **høyprioritetsfiler**, beregner fil **relevanseskårer** og filtrerer innledningsvis høyverdige repositories.
    *   **Intelligent Token-administrasjon**: Implementerer automatisk rotasjon og statussjekking av GitHub-tokens, dynamisk bytte av tilgjengelige tokens for å sikre kontinuiteten av overvåkingsoppgaver.
    *   **Databaselagring**: Bruker **SQLite**-databasen **`database/cve_record.db`** til å lagre CVE-poster, inkludert CVE-numre, beskrivelser, publiseringsdatoer, sist endrede datoer, repository-URL-er og annen informasjon.

*   **`github_monitor.py`**: **GitHub Repository-monitor**
    *   **Nøkkelordsøk**: Søker periodisk GitHub-repositories basert på `GITHUB_KEYWORDS`-listen definert i konfigurasjonsfilen **`config.py`**.
    *   **Overvåkingsliste**: Støtter `WATCHED_REPOSITORIES`-listen i konfigurasjonsfilen **`config.py`** for **fokusert overvåking** av forhåndsdefinerte sikkerhetsrepositories.
    *   **Repository-informasjonscrawling**: Henter detaljert repositoryinformasjon, inkludert beskrivelser, stjerneskårer, siste oppdateringstider, nylige commit-poster og mer.
    *   **Commit-postanalyse**: Crawler **nylige commit-poster** av repositories, **intelligent analyserer** commit-informasjon og filendringer, og bedømmer innledningsvis **sikkerhetsrelevansen** til repositories.
    *   **Svartelistefiltrering**: Støtter **brukersvartelister** og **repositorysvartelister** for å filtrere ut ugyldige informasjonskilder.
    *   **Intelligent Token-administrasjon**: Deler Token-administrasjonsmekanismen med CVE-monitoren.
    *   **Databaselagring**: Bruker **SQLite**-databasen **`database/github_repo.db`** til å lagre GitHub-repositoryposter, inkludert repositorynavn, URL-er, beskrivelser, siste oppdateringstider, stjerneskårer, om de er høyverdige repositories og annen informasjon.

### 2. AI-analysemodul (AI)

*   **`analyzer.py`**: **AI-analysator**
    *   **OpenAI & Gemini API**: Integrerer **OpenAI API** (primær) og **Gemini API** (backup), støtter **flermodell**-bytte, som `gpt-4o-mini-2024-07-18` (fallback-modell).
    *   **Prompt-engineering**: Designet **forskjellige Prompt-maler** for **forskjellige analysescenarier** (CVE-analyse, ny repositoryanalyse, repositoryoppdateringsanalyse, spesifikk overvåkingsrepositoryanalyse) for å optimalisere AI-analyseresultater.
    *   **JSON-formatutgang**: Krever at AI **strengt gir ut analyseresultater i JSON-format** for enkel programparsing og databehandling.
    *   **Flerdimensjonal sikkerhetsanalyse**: AI-analyseresultater inkluderer rik informasjon som **korte beskrivelser av sårbarheter/repositories**, **detaljerte sammendrag**, **risikonivåer**, **nøkkelpunkter**, **tekniske detaljer**, **berørte komponenter**, **verdivurderinger**, **sikkerhetstyper**, **oppdateringstyper** og **sårbarhetsutnyttelsesstatus**.
    *   **Resultatvalidering og standardisering**: Utfører **streng formatvalidering** og **innholdsstandardisering** på JSON-resultatene returnert av AI for å sikre nøyaktigheten og brukbarheten til dataene.
    *   **Dynamisk svartelisteoppdatering**: Basert på AI-analyseresultater, **automatisk bedømmer** om repositories eller brukere bør legges til i svartelisten og **dynamisk oppdaterer svartelistefilen**.
    *   **Analyseresultatpersistering**: **Lagrer** AI-analyseresultater som **JSON-filer** og **oppdaterer** tilsvarende poster i **databasen**.
    *   **Artikkeltittelklassifisering**: Støtter **AI-klassifisering** av sikkerhetsartikkeltitler for generering av sikkerhetsbriefingrapporter.
    *   **API-failover**: Når OpenAI API-kall mislykkes, **bytter automatisk** til **backup OpenAI API** eller **Gemini API** for å forbedre systemets **stabilitet og tilgjengelighet**.

### 3. Databehandling og administrasjon (Utils)

*   **`logger.py`**: **Logger**
    *   Bruker `logging`-modulen for å gi **komplett loggingsfunksjonalitet**, som dekker **DEBUG**, **INFO**, **WARNING**, **ERROR** og andre nivåer.
    *   Logginformasjon er **detaljert** og **strukturert**, noe som gjør det enkelt å feilsøke og overvåke systemet.
    *   Logger skrives ut til filen **`logs/security_monitor.log`** og rulles over daglig.

*   **`csv_writer.py`**: **CSV-resultatskriver** (for øyeblikket ikke brukt, kan utvides)
    *   Gir funksjonen for **eksportering av analyseresultater til CSV-filer** for enkel dataanalyse og deling.

*   **`article_fetcher.py`**: **Artikkelhenteren**
    *   **Henting fra flere kilder**: Støtter for øyeblikket henting av sikkerhetsartikler fra **BruceFeIix** og **D洞见 (doonsec)** WeChat offisielle kontoer.
    *   **Artikkeltittel- og URL-utvinning**: Bruker regulære uttrykk for å trekke ut artikkeltitler og URL-er fra nettsideinnhold.
    *   **Retry-mekanisme**: Bruker en **backoff-strategi** retry-mekanisme for å forbedre **stabiliteten og suksessraten** for artikkelhenting.
    *   **Artikkeltittelrensing**: **Standardiserer** og **renser** artikkeltitler, fjerner overflødige markører og formater.

*   **`article_manager.py`**: **Artikkeladministrator**
    *   **Artikkeldeduplisering**: **Filtrerer automatisk** behandlede artikkel-URL-er for å unngå duplikatanalyse og pushing.
    *   **AI-klassifikasjonsresultatbehandling**: Behandler AI-artikkeltittelklassifikasjonsresultater og **organiserer artikkellister etter kategori**.
    *   **Daglig sikkerhetsbriefingrapportgenerering**: **Regelmessig** genererer **Markdown-format** daglige sikkerhetsbriefingrapporter, oppsummerer de nyeste sikkerhetsartiklene og AI-analyseresultatene.
    *   **Automatisert bloggpublisering**: Kaller `blog_manager.py`-modulen for å **automatisk publisere daglige sikkerhetsbriefingrapporter til en bloggplattform**.
    *   **Artikkeldatapersistering**: **Lagrer** behandlede URL-er og klassifiserte artikler som **JSON-filer** for enkel påfølgende bruk og administrasjon.

*   **`blog_manager.py`**: **Bloggadministrator**
    *   **Bloggplattform API-interaksjon**: Kapsler inn **vanlige funksjoner** for interaksjon med bloggplattform-API-er, som **opprettelse av artikler** og **oppdatering av artikler**.
    *   **Artikkel-ID-kartleggingsadministrasjon**: **Registrerer** **artikkel-ID-ene** til daglige sikkerhetsbriefingrapporter på bloggplattformen for enkel påfølgende oppdatering og administrasjon.
    *   **Automatisert bloggpublisering**: Implementerer funksjonen for **automatisk publisering av daglige sikkerhetsbriefingrapporter til en bloggplattform**.

### 4. Database (Database)

*   **`database/models.py`**: **Databasemodelldefinisjon**
    *   Bruker **SQLAlchemy** til å definere to datamodeller, **`CVERecord`** (CVE-post) og **`Repository`** (GitHub-repositorypost), for å lette datalagring og spørring.
    *   Databasen bruker **SQLite**, og filbanene er **`database/cve_record.db`** og **`database/github_repo.db`**.

### 5. Konfigurasjonsfil (Config)

*   **`config.py`**: **Systemkonfigurasjonsfil**
    *   Administrerer sentralt systemets **konfigurasjonsparametere**, som databasebaner, API-nøkler, overvåkingsintervaller, nøkkelordslister, svartelister osv.
    *   Gjør det enkelt for brukere å **tilpasse** og **justere** systemadferd.
    *   Inkluderer følgende hovedkonfigurasjonseleementer:
        *   `DATABASE_PATH`: Databasefilbane
        *   `MONITOR_INTERVAL`: Overvåkingssyklusintervall (sekunder)
        *   `GITHUB_TOKEN`: GitHub API Token (støtter liste `GITHUB_TOKENS`)
        *   `GITHUB_KEYWORDS`: Liste over GitHub-repositorysøkenøkkelord
        *   `WATCHED_REPOSITORIES`: Liste over GitHub-repositories å fokusere overvåking på
        *   `BLACKLIST_USERS`: Brukersvarteliste
        *   `BLACKLIST_REPOSITORIES`: Repositorysvarteliste
        *   `PRIMARY_AI_CONFIG`: Primær AI-tjeneste (OpenAI) konfigurasjon
        *   `BACKUP_AI_CONFIGS`: Liste over backup AI-tjeneste (OpenAI) konfigurasjoner
        *   `GEMINI_AI_CONFIG`: Gemini AI-tjenestekonfigurasjon
        *   `BLOG_TOKEN`: Bloggplattform API Token

### 6. Hovedprogram (Main)

*   **`main.py`**: **Systemets hovedprogram**
    *   **Initialiserer** hver modul (monitorer, AI-analysator, artikkeladministrator osv.).
    *   **Starter** overvåkingssyklusen, **regelmessig** utfører CVE-overvåking, GitHub-repositoryovervåking, AI-analyse, artikkelhenting og bloggpubliseringsoppgaver.
    *   Bruker **flertråding** for å oppnå **samtidig overvåking** og **AI-analyse**, forbedrer systemeffektiviteten.
    *   **Unntaksbehandling** og **retry-mekanismer** sikrer stabil systemdrift.
    *   **Statusovervåkingstråd**: **Sjekker regelmessig** systemdriftsstatus og registrerer logger.
    *   **Daglig bloggpublisering**: **Regelmessig** automatisk publiserer daglige sikkerhetsbriefingrapporter til en bloggplattform.
    *   **Kommandolinjeoppstart**: Brukere kan starte og stoppe overvåkingssystemet via kommandolinjen.

## ⚙️ Kjøremiljø

*   Python 3.8+
*   Avhengigheter (se `requirements.txt`)

## 📦 Installasjonstrinn

1.  **Klon koderepository**

    ```bash
    git clone [Prosjektrepository-adresse]
    cd [Prosjektmappe]
    ```

2.  **Installer avhengigheter**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Konfigurer `config.py`-filen**

    *   Konfigurer GitHub API Token (`GITHUB_TOKEN` eller `GITHUB_TOKENS`)
    *   Konfigurer OpenAI API-nøkkel og Base URL (`PRIMARY_AI_CONFIG`, `BACKUP_AI_CONFIGS`)
    *   Konfigurer Gemini API-nøkkel og Base URL (`GEMINI_AI_CONFIG`)
    *   Konfigurer bloggplattform API Token (`BLOG_TOKEN`) (hvis du trenger å publisere automatisk til en blogg)
    *   Endre andre konfigurasjonselementer etter behov, som overvåkingsintervall, nøkkelordsliste, svarteliste osv.

4.  **Kjør systemet**

    ```bash
    python main.py
    ```

## 📝 Fremtidige planer

*   **Støtte for flere datakilder**: Utvid støtten for flere sikkerhetsinformasjonskilder, som sikkerhetssamfunn, sårbarhetsplattformer osv.
*   **Mer raffinert AI-analyse**: Kontinuerlig optimalisering av Prompt-engineering for å forbedre nøyaktigheten og dybden av AI-analyse.
*   **Rikere funksjoner**: Som sårbarhetsvarslinger, truselintelligensvisualisering, tilpassede rapporter osv.
*   **Web UI-administrasjonsgrensesnitt**: Utvikle et Web UI-administrasjonsgrensesnitt for å gjøre det enkelt for brukere å konfigurere og administrere overvåkingssystemet.

## 🤝 Bidrag

Bidrag er velkomne! Hvis du har forslag eller feilrapporter, vennligst send inn en Issue eller Pull Request.

## 📜 Lisens

Dette prosjektet er lisensiert under MIT-lisensen - se [LICENSE](LICENSE)-filen for detaljer.

---

**Takk for din oppmerksomhet!** ⭐ **Stjern** dette prosjektet for å støtte vårt arbeid!