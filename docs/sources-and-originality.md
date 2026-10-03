# Sources and originality

## Intellectual boundary

Reach Signal is independently written software. Its structure, interface, wording, formulas as implemented, fictional examples, documentation and visual identity were created for this repository.

It does not reproduce lecture slides, speaker notes, classroom cases, assignments, exam material, course diagrams or institution-specific teaching material. General topics such as trade areas, catchments, retail gravity models and site selection only define the problem domain. The implementation rests on public publications and standard geometry.

The Oslo-area café example (areas such as *Centre*, *North* and *Outer east*; the *Existing centre café*, two competitors and two candidates), its coordinates, demand and attractiveness values are written in code and wholly fictional. They are not market evidence, official population data or measured travel times.

## What the sources support

The app's **Research & limits** page and every printable brief and evidence ZIP carry the source list.

- **Huff (1963, 1964)** define the probabilistic trade-area model: the chance that a customer in one area chooses a centre rises with the centre's size and falls with travel time, relative to all alternatives. Reach Signal implements this share rule with distance or travel time.
- **Nakanishi and Cooper (1974)** develop the multiplicative competitive interaction form with exponents on each attraction variable, estimated by least squares. Reach Signal uses an exponent on attractiveness in the same spirit but does not estimate it.
- **De Beule, Van den Poel and Van de Weghe (2014)** and **Dolega, Pavlis and Singleton (2016)** show how Huff-type models are extended and applied to real retail networks and centres. They are cited for the case that parameters and attractiveness need local estimation, which Reach Signal leaves to the user.
- **Moritz (2000)** documents the Geodetic Reference System 1980, whose mean Earth radius of 6,371,008.7714 m gives the 6,371.0088 km used for straight-line distances.
- **Esri's ArcGIS Pro documentation** on the Huff model describes the model as used in commercial site-analysis software. It is cited for orientation, not as validation.

The outside option, the minimum modeled distance, the access threshold, the default parameter values and the sensitivity grid are this app's transparent design choices. No source validates them.

## Primary references

- De Beule, M., Van den Poel, D., & Van de Weghe, N. (2014). An extended Huff-model for robustly benchmarking and predicting retail network performance. *Applied Geography, 46*, 80–89. https://doi.org/10.1016/j.apgeog.2013.09.026
- Dolega, L., Pavlis, M., & Singleton, A. (2016). Estimating attractiveness, hierarchy and catchment area extents for a national set of retail centre agglomerations. *Journal of Retailing and Consumer Services, 28*, 78–90. https://doi.org/10.1016/j.jretconser.2015.08.013
- Huff, D. L. (1963). A probabilistic analysis of shopping center trade areas. *Land Economics, 39*(1). https://doi.org/10.2307/3144521
- Huff, D. L. (1964). Defining and estimating a trading area. *Journal of Marketing, 28*(3), 34–38. https://doi.org/10.1177/002224296402800307
- Moritz, H. (2000). Geodetic Reference System 1980. *Journal of Geodesy, 74*(1), 128–133. https://doi.org/10.1007/s001900050278
- Nakanishi, M., & Cooper, L. G. (1974). Parameter estimation for a multiplicative competitive interaction model: Least squares approach. *Journal of Marketing Research, 11*(3), 303–311. https://doi.org/10.1177/002224377401100309
- Esri. How Huff Model works. ArcGIS Pro documentation. https://doc.esri.com/en/arcgis-pro/latest/tool-reference/business-analyst/understanding-huff-model.html
- Esri. Create a Huff model. ArcGIS Pro documentation. https://doc.esri.com/en/arcgis-pro/latest/help/analysis/business-analyst/huff-model-overview.html

Bibliographic details of the journal articles were checked against Crossref.

## License

Reach Signal is free software under AGPL-3.0-or-later. The license covers this project's expression, not ownership of published methods. The embedded interface font is distributed under the SIL Open Font License; see `src/reachsignal/ui/assets/fonts/OFL.txt`.
