# Methods

Reach Signal allocates a fixed, user-supplied demand between listed locations and an outside option with a Huff choice model. It is a scenario tool: every number depends on the demand, attractiveness, distance and parameter values you enter.

## 1. Inputs and review

A case declares a demand unit, a period and the meaning of site attractiveness, and lists customer areas (demand `D_i`, outside weight `O_i`, optional coordinates), locations (role own, competitor or candidate; attractiveness `A_j`; optional coordinates), optional travel times and sources. The four model settings are the attractiveness exponent α, distance decay β, the minimum modeled distance `floor` and the access threshold.

Imports arrive as unreviewed drafts. Results appear only after a named reviewer records what they checked; the review stores a SHA-256 fingerprint of the inputs, and any edit clears it.

## 2. Distances

- **Straight line:** the Haversine great-circle distance in kilometres on a sphere of radius 6,371.0088 km, the mean Earth radius of the Geodetic Reference System 1980 (Moritz, 2000). Longitudes that cross the date line are handled.
- **Travel time:** the minutes you supply for each area × location pair. A missing pair is a missing input; the app never substitutes a straight-line distance.

## 3. Huff allocation with an outside option

For area *i* and site *j* in the scenario:

```
H_ij = A_j^α / max(d_ij, floor)^β
P_ij = H_ij / (Σ_k H_ik + O_i)          share of area i's demand going to site j
P_i0 = O_i  / (Σ_k H_ik + O_i)          share going to the outside option
allocated_j = Σ_i D_i · P_ij
```

This is Huff's (1963, 1964) probabilistic trade-area model with the common generalisation of an exponent on attractiveness (the multiplicative competitive interaction form of Nakanishi and Cooper, 1974). The outside weight `O_i` is this app's extension: it represents alternatives that are not listed, or not visiting, on the same attraction scale. With `O_i = 0` the listed sites share all of the area's demand.

The minimum modeled distance stops a site at (almost) zero distance from taking all demand. Raw distances are kept for access and in the pair table; the app reports how many pairs were raised to the floor.

Computation uses log weights shifted by each area's maximum before exponentiating, so very large or small weights do not overflow.

## 4. Baseline and candidates

The baseline holds own and competitor sites. Each candidate is added on its own to the same baseline, with demand and everything else fixed. For each candidate the app reports:

- its allocated demand;
- the change in the own portfolio (existing own sites plus the candidate);
- the change for existing own sites (the demand it takes from them), for competitors and for the outside option.

Because total demand is fixed, the candidate's allocation equals the sum of what existing own sites, competitors and the outside option lose. Adding candidate *c* only adds `H_ic` to each area's denominator, so all candidates are computed in one pass over the areas from the baseline sums; a test checks this against allocating each scenario separately.

## 5. Access

Independently of the Huff shares, the app reports the demand in areas whose nearest listed site (including competitors) lies beyond the access threshold, in the baseline and with each candidate. The threshold is a planning criterion you choose, not a measure of service quality.

## 6. Sensitivity

The candidate comparison is repeated for β = 0.5, 1.0, 1.5, 2.0 and 3.0, with attractiveness, outside weights and demand fixed. If the ranking of candidates changes inside a plausible range of β, the decision depends on an assumption that needs local evidence. This is an assumption check, not a confidence interval.

## 7. Calibration is outside the app

β, α and the outside weights should be calibrated against observed customer origins (loyalty-card or transaction postcodes, surveys, visit counts by area) before modeled allocations are read as forecasts. Nakanishi and Cooper (1974) estimate the parameters of this model family by least squares; De Beule, Van den Poel and Van de Weghe (2014) extend the Huff model to benchmark and predict the performance of a retail network; Dolega, Pavlis and Singleton (2016) estimate attractiveness and catchment extents for retail centres nationally. Reach Signal implements none of these estimation methods; it keeps the parameters visible so a calibrated value can be entered.

## 8. Large cases

The engine processes customer areas in blocks of about one million area × location cells, so memory grows with the number of areas and locations, not with their product. Validation is done column by column. Results for the current inputs are computed once per change in the app, not on every click.

There are no app-imposed limits on the number of areas or locations on your own computer; memory is the limit, and running out of it is reported as a plain message. A public demo (`SIGNAL_PUBLIC=1`) applies the caps listed in the [data guide](data-guide.md#data-limits).

What is shortened is display only, and each place says so:

- the map aggregates areas into a grid of about 60 × 60 cells above 3,000 areas (demand-weighted colours);
- on-screen tables show their largest 10,000 rows;
- the pair-level allocation table in the app and the Excel file covers the first areas up to 100,000 rows; the Evidence ZIP writes every area × location row, block by block;
- the printable brief shows 200 rows per table.

Measured on a synthetic case of 200,000 customer areas and 50 locations (10 candidates) on a Windows desktop shared with other work:

| Step | Time |
|---|---|
| Read the two CSV files (7.9 MB) | 1.0 s |
| Map columns and build the case | 1.8 s |
| Validate the case | 0.7 s |
| Baseline allocation | 1.5 s |
| One candidate scenario | 1.4 s |
| All 10 candidate comparisons | 1.5 s |
| Distance-decay sensitivity (5 values) | 2.2 s |
| Printable brief | 4.7 s |
| Evidence ZIP | 12 s |
| Excel export | 30–42 s |
| Import that Excel export again | 43 s |

The process peak working set for the whole sequence, including the exports, was about 630 MB.

## 9. What it does not do

It does not estimate demand, sales, profit, market share, capacity or congestion; fit parameters; route on a road network or geocode addresses; model several new sites opening together; or recommend a site. Customer-area centroids simplify where people live and travel.
