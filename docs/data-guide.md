# Data guide

Reach Signal reads customer areas and locations from Excel or CSV, from a saved project JSON, or from a JSON draft returned by an AI. The **1 · Add your data** page offers fictional starting points: a simple Excel example, a complete project workbook and one CSV example per table.

All spreadsheets need headings in the first row. CSV files must be UTF-8 (a byte-order mark is fine) and may use a comma, semicolon or tab delimiter. Choose dot or comma decimals in the app; thousands separators are rejected. Blank numeric cells stay unknown, never zero, and a calculation waits until every input it needs is filled in.

## Simple business tables: areas and locations

Use two sheets in one workbook, or two CSV files uploaded together. This layout always uses straight-line kilometres.

**Customer areas**, one row per area (a district, postcode, grid cell or store-trade zone):

| Area name | Latitude | Longitude | Demand | Outside-option weight | Assumption or evidence note |
|---|---|---|---|---|---|
| Example centre | 59.915 | 10.750 | 1200 | 0.15 | Fictional area |

- `Area name`: required and unique (names are compared without case).
- `Latitude`, `Longitude`: decimal degrees for the area's centroid, both or neither. Latitudes must lie within ±85°.
- `Demand`: zero or more, in the one unit you declare in the app (residents, potential visits, spending). Population stays population; the app never turns it into visits or sales.
- `Outside-option weight`: zero or more, on the same scale as attractiveness. It stands for alternatives you have not listed, or not visiting at all. It is a weight, not a percentage. Zero forces all demand to the listed sites.

**Locations**, one row per site:

| Location name | Location type | Latitude | Longitude | Site attractiveness | Assumption or evidence note |
|---|---|---|---|---|---|
| Example existing café | Own | 59.915 | 10.740 | 1 | Fictional site |
| Example competitor | Competitor | 59.930 | 10.820 | 1.1 | Fictional site |
| Example candidate | Candidate | 59.966 | 10.752 | 0.9 | Fictional site |

- `Location type`: `Own`, `Competitor` or `Candidate` (synonyms such as *owned*, *rival* or *proposed* are recognised). At least one own or competitor site is needed for the baseline.
- `Site attractiveness`: one positive, comparable measure for every site, for example floor area in square metres or an index with your existing site at 1. A candidate with unknown attractiveness is listed as missing inputs; it is never treated as zero.

In the app you also state what demand measures, the period, what attractiveness means, and four model settings: the attractiveness exponent α (0.1 to 5, default 1), distance decay β (0 to 5, default 1.5), the minimum modeled distance (default 0.25 km) and the access threshold (default 5 km). The defaults are starting assumptions, not estimates.

## Complete project workbook

This is the layout the Excel export writes, and the only spreadsheet layout that carries travel times. Sheets are linked by reference columns:

| Sheet | Contents |
|---|---|
| Case | The case brief |
| Scope | Demand unit, period, definition of attractiveness |
| Model settings | Distance method (`straight_km` or `travel_minutes`), α, β, minimum distance, access threshold |
| Customer areas | Reference, name, coordinates, demand, outside weight, source reference, note |
| Locations | Reference, name, role (`own`, `competitor`, `candidate`), coordinates, attractiveness, source reference, note |
| Travel times | Area reference, location reference, travel time in minutes |
| Sources | Reference, title, public URL or blank, note |

References start with a letter and use letters, digits, `_` or `-` (up to 40 characters). `OUTSIDE` is reserved. In travel-time mode every area needs a time to every baseline site, and to a candidate before that candidate can be compared. Straight-line distance is never substituted for a missing travel time. Result sheets in an exported workbook are skipped on import.

## Size limits

| Limit | Value |
|---|---|
| Upload size | 1,000 MB (launcher default; `REACHSIGNAL_MAX_UPLOAD_MB`) |
| Rows per sheet or CSV | 1,000,000 |
| Cells per upload | 10,000,000 |
| Customer areas | 500,000 |
| Locations (all roles) | 500 |
| Travel-time pairs | 1,000,000 |
| Areas × locations | 25,000,000 |

The model always uses every area. When a case is too large, aggregate small areas (postcodes into districts, or a coarser grid) or remove locations you do not need. For very large tables, CSV reads in seconds where Excel takes minutes; the Excel export of a 200,000-area case takes well under a minute to write, and longer to import again.

## What gets rejected

The import stops and says why when it finds: repeated names or references; a reference to a missing area, location or source; only one of two coordinates; negative demand or outside weight; attractiveness of zero or below; out-of-range latitudes or longitudes; duplicate travel-time pairs; no own or competitor site; text where a number belongs; percent signs in ordinary number columns; formulas without a saved result (recalculate and save in Excel first); Excel error cells; more than 30 sheets or 80 columns; or the old `.xls` format (save as `.xlsx`).

## Before you upload

1. Choose one demand unit and one period, and say where the numbers come from.
2. Choose one attractiveness measure that means the same thing for your sites and competitors.
3. Decide what the outside option represents (unlisted competitors, online, not visiting) and set its weight on the same scale.
4. Use travel times when roads, water or transit make straight lines misleading, and keep one transport mode and time of day throughout.
5. Treat the default α, β and outside weights as assumptions to test, not facts.
