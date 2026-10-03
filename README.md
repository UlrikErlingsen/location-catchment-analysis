<p align="center">
  <img src="assets/reachsignal-banner.png" alt="Reach Signal: Where could a new location reach, and how would it share demand with existing sites?" width="100%">
</p>

<p align="center">
  <a href="https://github.com/UlrikErlingsen/location-catchment-analysis/actions"><img alt="Tests" src="https://github.com/UlrikErlingsen/location-catchment-analysis/actions/workflows/tests.yml/badge.svg"></a>
  <a href="https://github.com/UlrikErlingsen/signal-hub"><img alt="Signal · Market" src="https://img.shields.io/badge/Signal-Market-728157?labelColor=2e2b25"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-2e2b25?logo=python&logoColor=f9f4ed">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-app-728157?logo=streamlit&logoColor=f9f4ed">
  <a href="LICENSE"><img alt="License: AGPL-3.0-or-later" src="https://img.shields.io/badge/License-AGPL--3.0--or--later-645c50"></a>
</p>

<p align="center"><strong>See which customer areas a new site could reach, and where its demand would come from.</strong></p>

**Reach Signal** helps retail, hospitality and service marketers compare candidate locations before they commit to one. It combines customer areas, your own sites, competitors and candidates in a Huff choice model on straight-line distance or supplied travel times, and shows how each candidate would share a fixed demand with the sites that already exist.

> Where could a new location reach, and how would it share demand with existing sites?

Everything runs locally with open-source Python packages. There is no account, telemetry, external AI call, remote database, map tile server or built-in persistence.

## Read this first

> **A modeled catchment is not observed demand.** Reach Signal allocates the demand you supply according to distance and attractiveness assumptions you choose. It does not know where your customers actually come from.

- **The distance-decay parameter is an assumption unless you calibrate it.** The app starts at β = 1.5 and shows how the candidate ranking moves between β = 0.5 and 3.0, but it does not fit β, the attractiveness exponent or the outside-option weights to your data. Calibrate them against observed visits, loyalty-card origins or sales by area before using the numbers as forecasts.
- **Total demand stays fixed.** Every scenario reallocates the same demand between your sites, competitors and an explicit outside option. A new site never creates demand in this model; it only moves it.
- **Candidates are evaluated one at a time.** Each comparison adds one candidate to the same baseline. Opening two sites at once needs its own scenario.
- **The map is a local schematic.** It is drawn from coordinates without streets, boundaries or map tiles. Straight-line kilometres ignore roads, water and other barriers; supply a travel-time matrix when that matters.

## Scope

**Version 1.0 supports:**

- customer areas with demand, an outside-option weight and optional coordinates, and own, competitor and candidate locations with one comparable attractiveness measure;
- a Huff model, `A^α / d^β`, with an explicit outside option, on straight-line (Haversine) kilometres or a complete area × location matrix of travel minutes;
- the baseline catchment, each candidate's allocation, its effect on your existing sites, competitors and the outside option, and a distance-decay sensitivity check;
- an access threshold that reports demand lying beyond a chosen distance from any site;
- large cases with no app-imposed limits on your own computer: hundreds of thousands of customer areas are computed in full, in blocks that keep memory in check;
- Excel or CSV upload, manual entry, and an optional copy-and-paste AI prompt for structuring research;
- Excel, project JSON, a printable HTML brief and an evidence ZIP.

**It does not:** estimate demand, sales, profit, market share or capacity; fit or calibrate model parameters; route on a road network or geocode addresses; model several new sites opening together; draw real map backgrounds; or recommend a site. Whether a location project deserves investment at all is **[Gate Signal](https://github.com/UlrikErlingsen/launch-decision-gate)**'s question, and **[Shift Signal](https://github.com/UlrikErlingsen/cannibalization-analysis)** asks the new-or-moved question for a product launch rather than a site.

## Try the demo in three minutes

1. Start the app. **Overview** opens on a fictional Oslo-area café case: 8 customer areas with 10,150 potential visits a month, one existing café, two competitors and two candidate sites. The demo comes with a recorded fictional review, so results show straight away.
2. Open **3 · Catchment map**. In the baseline, the existing café is allocated about 2,910 visits and about 2,765 go to the outside option. Switch **Scenario** to *North candidate* and watch the map and the allocation table change.
3. Open **4 · Candidate comparison**. The North candidate is allocated about 1,734 visits and raises the own portfolio by about 1,434, because about 300 move from the existing café. Below, the sensitivity chart shows that North stays ahead of Outer-east for every β from 0.5 to 3.0.
4. Open **5 · Export** and download the Excel workbook, the printable brief or the evidence ZIP.

The demo is synthetic data written for this app. Its coordinates, demand and attractiveness are invented; it represents no real business, official population data, measured travel times or empirical finding.

## Data contract

Two spreadsheet layouts, plus JSON. Excel `.xlsx` or UTF-8 CSV (comma, semicolon or tab), with headings in the first row. Column names are matched for you and can be corrected before import. Blank numbers stay unknown, never zero, and a calculation waits until every input it needs is filled in.

**Simple business tables** (straight-line kilometres): one table of customer areas and one of locations. Demand unit, period, the meaning of attractiveness and the model settings are entered in the app.

| Area name | Latitude | Longitude | Demand | Outside-option weight |
|---|---|---|---|---|
| Example centre | 59.915 | 10.750 | 1200 | 0.15 |

| Location name | Location type | Latitude | Longitude | Site attractiveness |
|---|---|---|---|---|
| Example existing café | Own | 59.915 | 10.740 | 1 |
| Example candidate | Candidate | 59.966 | 10.752 | 0.9 |

**Complete project workbook**: the sheets *Case*, *Scope*, *Model settings*, *Customer areas*, *Locations*, *Travel times* and *Sources*, linked by reference columns. This is the layout the Excel export writes, and the one that carries a travel-time matrix (one row per area × location, in minutes).

A file or case is rejected, with the reason shown, for: repeated area or location names or IDs, a reference to a missing area, location or source, only one of two coordinates, negative demand, attractiveness of zero or below, latitudes outside ±85°, duplicate travel-time pairs, no existing own or competitor site, ambiguous decimal separators, percent signs in ordinary number columns, formulas without a saved result, Excel error cells, or the old `.xls` format.

See the [data guide](docs/data-guide.md).

### Data limits

**On your own computer there are none.** Standalone, in a local Signal Hub or on a company's own server, Reach Signal sets no limit on file size, rows, cells, customer areas or locations; the computer's memory is the limit. Streamlit's upload cap defaults to 10,000 MB (`REACHSIGNAL_MAX_UPLOAD_MB` in the launchers, `STREAMLIT_SERVER_MAX_UPLOAD_SIZE` in Docker). If a file or calculation does not fit in memory, the app says so in plain words instead of crashing. CSV reads much faster than Excel for very large tables, and one Excel sheet holds at most 1,048,575 rows (longer exported tables continue on further sheets, which the importer joins again).

**A public demo** (`SIGNAL_PUBLIC=1`, as on a shared Hub server) applies hard caps, and says so when one is reached:

| Demo cap (`SIGNAL_PUBLIC=1` only) | Value |
|---|---|
| Upload size | 50 MB |
| Project or AI JSON file | 50 MB |
| Pasted AI reply | 2,000,000 characters |
| Rows per sheet or CSV | 200,000 |
| Columns per sheet; sheets per workbook | 80; 30 |
| Cells per upload | 2,000,000 |
| Customer areas | 50,000 |
| Locations (all roles) | 100 |
| Travel-time pairs | 200,000 |
| Areas × locations | 2,000,000 |

## Analysis contract

Before any result is shown, the case declares what demand measures (residents, visits or spending), for which period, and what site attractiveness means, so that one unit runs through every row. Model settings (attractiveness exponent α, distance decay β, minimum modeled distance and access threshold) are visible inputs, not hidden defaults. A named reviewer must then record what they checked; the review is tied to a SHA-256 fingerprint of the inputs, and any edit clears it. Imports from spreadsheets or an AI always arrive as unreviewed drafts.

## Methods

1. **Validate:** schema, bounds and references are checked column by column, so 200,000 rows validate in under a second.
2. **Distances:** Haversine kilometres on a sphere of radius 6,371.0088 km, or the supplied travel minutes. Distances below the minimum modeled distance are raised to it in the model (and reported), so a site at zero distance cannot take all demand.
3. **Huff allocation:** for area *i* and site *j*, `H_ij = A_j^α / max(d_ij, floor)^β`. Each area's demand `D_i` is shared in proportion to `H_ij`, with an outside weight `O_i` for alternatives not listed or no visit: `P_ij = H_ij / (Σ_k H_ik + O_i)`. The outside weight is this app's extension of Huff's model and shares the attraction scale.
4. **Candidates:** the baseline holds own and competitor sites. Each candidate is added on its own; the app reports its allocation and the change for your existing sites, competitors and the outside option, which add up to zero.
5. **Access:** demand in areas whose nearest listed site is beyond the access threshold, independent of the Huff shares.
6. **Sensitivity:** the comparison is repeated for β = 0.5, 1.0, 1.5, 2.0 and 3.0, everything else fixed.

The engine works on arrays in blocks of areas, so memory grows with the number of areas, not with areas × locations. On a synthetic 200,000-area × 50-location case (10 candidates) on a desktop PC, reading and checking the CSV files took about 3 s, the baseline about 1.5 s, all candidate comparisons about 1.5 s and the five-step sensitivity about 2 s, with a process peak below 650 MB. Only what is drawn on screen is shortened: the map aggregates areas into a grid above 3,000 areas, on-screen tables show their largest 10,000 rows, the pair-level allocation table in the app and the Excel file covers at most 100,000 rows, and the printable brief shows 200 rows per table. Each says so where it happens; every calculation uses all areas, and the Evidence ZIP holds every row.

See [methods](docs/methods.md).

## Decision statuses

Reach Signal does not pick a site. It shows one of these states:

- **UNREVIEWED DRAFT**: inputs are visible and editable, but no modeled results are shown until a review is recorded.
- **MISSING INPUTS**: the baseline or a candidate lacks demand, an outside weight, attractiveness, coordinates or travel minutes; the calculation is withheld and the missing items are listed.
- **COMPLETE**: the scenario is calculated under the stated assumptions. A candidate row reads *Complete* or *Missing inputs: …*.

Warnings sit beside the results: a zero outside weight (a closed choice set), distances raised to the minimum modeled distance, and a geographic extent too broad for the local map.

## Exports

From **5 · Export**, each file is prepared when you click it:

- **Excel workbook**: the case brief, every input table in the importable layout, and, once the case is reviewed and complete, result sheets (baseline allocations, area access and choice, the pair-level allocation table for the first 100,000 rows, and the candidate comparison). Review signatures are not carried through Excel; a re-imported workbook needs a new review.
- **Project JSON**: the full case with its origin and review record, which can be restored in the app.
- **Printable brief**: HTML with units, inputs, results, sources, limits and references, ready to print or save as PDF.
- **Evidence ZIP**: `project.json`, `brief.html`, `references.json` and every table as CSV, including the full area × location allocation table, with the project's SHA-256 fingerprint.

Exports contain your full input rows, so treat them like the source data. CSV text beginning with `=`, `+`, `-` or `@` is prefixed with an apostrophe, and Excel text cells are stored as literal text, so neither is read as a formula.

## Run locally

You need Python 3.10 or newer and a local copy of this folder.

**macOS:** double-click `run_app.command`. **Windows:** double-click `run_app.bat`.

The first launch creates a private `.venv` and downloads open-source dependencies. Later launches reuse it. Or use a terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open the local address shown in the terminal. Reach Signal prefers local port 8599; the macOS launcher falls back to another free port if it is taken. Both launchers accept `REACHSIGNAL_PORT` and `REACHSIGNAL_MAX_UPLOAD_MB` (default 10000), and the macOS launcher also accepts `REACHSIGNAL_NO_BROWSER=1`.

### Docker

```bash
docker build -t reachsignal .
docker run --rm -p 8599:8599 reachsignal
```

Then open http://127.0.0.1:8599. The container runs as a non-root user and accepts uploads up to 10,000 MB (`STREAMLIT_SERVER_MAX_UPLOAD_SIZE`). Set `SIGNAL_PUBLIC=1` for a public demo with the caps above.

## Privacy

Uploaded files are processed in memory by the running Streamlit app; nothing is sent to an external service and nothing is written to disk except the files you download. Inside Signal Hub the app writes no files, makes no network calls and keeps the case only in your session; on any hosted deployment the operator is responsible for transport security, access control, logs and retention. See [PRIVACY.md](PRIVACY.md).

## No install? Give this file to an AI

[AI_ANALYST.md](AI_ANALYST.md) is a standalone analysis protocol for a capable AI assistant, with the same scope limits, calculations and honesty rules. The local app is the more private option, and the only practical one for large area tables: a cloud AI sees whatever you upload or paste.

## Development

```bash
python -m pip install -e ".[test]"
python -m pytest
python -m ruff check .
python -m build
```

The model core installs without Streamlit or Plotly; `pip install -e ".[ui]"` adds the app dependencies. Tests cover hand-computed Huff shares with an outside option, demand conservation, candidate reallocation identities, the Haversine distance, the distance floor, missing-input handling, agreement between the one-pass comparison and scenario-by-scenario allocation on a 20,000-area case, fast validation, no limits locally and enforced caps on a public demo, the full pair table in the ZIP, Excel continuation sheets, Excel and CSV round trips, spreadsheet-safe exports, every Streamlit page, and the Signal Hub contract (`reachsignal.ui.render`, namespaced keys, Hub mode, no repo-root file reads).

## Where this fits in Signal

Reach Signal supplies the modeled catchment that **[Gate Signal](https://github.com/UlrikErlingsen/launch-decision-gate)** can weigh when it decides whether a new location deserves the next investment. **[Shift Signal](https://github.com/UlrikErlingsen/cannibalization-analysis)** asks the same new-or-moved question for a product launch, and **[Prospect Signal](https://github.com/UlrikErlingsen/b2b-prospecting)** turns a chosen market into a ranked list of Norwegian companies to approach.

<!-- signal-suite:start (generated from signal-hub/apps.yaml by scripts/sync_readme_suite.py) -->
| Family | App | Asks |
|---|---|---|
| Brand | [Track Signal](https://github.com/UlrikErlingsen/brand-tracking) | Is the brand moving, or is the tracker just noisy? |
| Brand | [Position Signal](https://github.com/UlrikErlingsen/brand-positioning) | Where do brands sit relative to competitors? |
| Market | [Prospect Signal](https://github.com/UlrikErlingsen/b2b-prospecting) | Which Norwegian companies fit your ideal customer, and which first? |
| Market | [Listen Signal](https://github.com/UlrikErlingsen/media-listening) | Who is talking about the brand in Norwegian media, and in what tone? |
| Market | [Influence Signal](https://github.com/UlrikErlingsen/influencer-campaigns) | Which creators delivered, and was every post labelled properly? |
| Market | [Season Signal](https://github.com/UlrikErlingsen/marketing-calendar) | What does the Norwegian marketing year look like, worked backwards? |
| Market | [Adopt Signal](https://github.com/UlrikErlingsen/adoption-forecasting) | When will a new product be adopted? |
| Market | [Rival Signal](https://github.com/UlrikErlingsen/competitor-analysis) | Which rivals matter, and how could they respond? |
| Market | **Reach Signal** (this app) | Where could a new location reach, and how would it share demand with existing sites? |
| Customer | [Worth Signal](https://github.com/UlrikErlingsen/customer-value-analytics) | What are customers and relationships worth? |
| Customer | [Segment Signal](https://github.com/UlrikErlingsen/customer-segmentation) | Do customers form stable, useful groups? |
| Customer | [Trace Signal](https://github.com/UlrikErlingsen/journey-path-analysis) | How do logged customer journeys actually unfold? |
| Customer | [Blueprint Signal](https://github.com/UlrikErlingsen/service-blueprinting) | How is the customer experience actually delivered, and where do the handoffs fail? |
| Customer | [Recommend Signal](https://github.com/UlrikErlingsen/recommender-evaluation) | Which recommendation policy should be tested live? |
| Research | [Choice Signal](https://github.com/UlrikErlingsen/conjoint-analysis) | How do product attributes drive choice? |
| Research | [Driver Signal](https://github.com/UlrikErlingsen/survey-driver-analysis) | Which measured experiences move with satisfaction? |
| Research | [Measure Signal](https://github.com/UlrikErlingsen/measurement-validation) | Does a multi-item score have a defensible structure? |
| Research | [Text Signal](https://github.com/UlrikErlingsen/open-text-analysis) | What recurring patterns appear in open-ended responses? |
| Research | [Tag Signal](https://github.com/UlrikErlingsen/pricing-analysis) | What price range is supported, and how does profit move? |
| Research | [Learn Signal](https://github.com/UlrikErlingsen/research-prioritization) | Which uncertainty is worth paying to research before you decide? |
| Decide | [Experiment Signal](https://github.com/UlrikErlingsen/experiment-analysis) | Did the treatment cause a practically meaningful change? |
| Decide | [Gate Signal](https://github.com/UlrikErlingsen/launch-decision-gate) | Does a concept deserve the next investment? |
| Decide | [Shift Signal](https://github.com/UlrikErlingsen/cannibalization-analysis) | Does a launch grow the portfolio, or move existing demand around? |
| Decide | [Alloc Signal](https://github.com/UlrikErlingsen/marketing-mix-allocation) | Where should the next marketing budget go? |

All 24 apps run side by side in [Signal Hub](https://github.com/UlrikErlingsen/signal-hub), each opening with fictional demo data. Every repo carries the [`signal-suite`](https://github.com/topics/signal-suite) topic, and the suite is listed at [ulrikerlingsen.com](https://ulrikerlingsen.com). Freddo CRM is a separate product.
<!-- signal-suite:end -->

## References

- Huff, D. L. (1963). A probabilistic analysis of shopping center trade areas. *Land Economics, 39*(1). https://doi.org/10.2307/3144521
- Huff, D. L. (1964). Defining and estimating a trading area. *Journal of Marketing, 28*(3), 34–38. https://doi.org/10.1177/002224296402800307
- Nakanishi, M., & Cooper, L. G. (1974). Parameter estimation for a multiplicative competitive interaction model: Least squares approach. *Journal of Marketing Research, 11*(3), 303–311. https://doi.org/10.1177/002224377401100309
- De Beule, M., Van den Poel, D., & Van de Weghe, N. (2014). An extended Huff-model for robustly benchmarking and predicting retail network performance. *Applied Geography, 46*, 80–89. https://doi.org/10.1016/j.apgeog.2013.09.026
- Dolega, L., Pavlis, M., & Singleton, A. (2016). Estimating attractiveness, hierarchy and catchment area extents for a national set of retail centre agglomerations. *Journal of Retailing and Consumer Services, 28*, 78–90. https://doi.org/10.1016/j.jretconser.2015.08.013
- Moritz, H. (2000). Geodetic Reference System 1980. *Journal of Geodesy, 74*(1), 128–133. https://doi.org/10.1007/s001900050278
- Esri. How Huff Model works. ArcGIS Pro documentation. https://doc.esri.com/en/arcgis-pro/latest/tool-reference/business-analyst/understanding-huff-model.html

The citations define the model family and show how it is calibrated in practice. None of them validates this app's default settings, its outside-option extension or its access threshold, and the app does not implement the calibration methods they describe.

## Originality and license

Reach Signal is an independent implementation based on public literature and original synthetic examples. It does not reproduce lecture slides, institution-specific cases, teaching diagrams, exercises, exam questions, screenshots, tables or other institution-specific teaching material. See [sources and originality](docs/sources-and-originality.md).

The software and documentation are free under AGPL-3.0-or-later. The license covers this project's expression, not ownership of published methods.

This application was developed with AI coding assistance and checked through source review, analytical fixtures, deterministic synthetic tests, automated app tests and visual inspection. Verify material decisions independently; no warranty is provided.

---

<p>
  <img src="assets/reachsignal-mark-64.png" width="20" height="20" alt="" align="absmiddle">
  <strong>Reach Signal</strong> is part of <a href="https://github.com/UlrikErlingsen/signal-hub"><strong>Signal</strong></a>, open marketing-evidence tools by <a href="https://ulrikerlingsen.com">Ulrik Erlingsen</a>.
</p>
