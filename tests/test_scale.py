"""Large cases at a moderate, fast scale: the vectorized engine must agree with the scenario-by-scenario definition,
conserve demand, and shorten only what it displays (and say so)."""
from io import BytesIO

from openpyxl import load_workbook
import numpy as np
import pandas as pd
import pytest

from reachsignal import input_format as fmt, model, portable as io, spreadsheets as sheets

AREAS, SITES, CANDIDATES = 20_000, 25, 5


def large_case(n=AREAS, s=SITES, candidates=CANDIDATES, travel=False, seed=11):
    rng = np.random.default_rng(seed)
    d = model.starter("Synthetic large case")
    d["context"] = [{"demand_unit": "Residents", "period": "2026", "attractiveness_definition": "Index"}]
    lat, lon = 59.9 + rng.normal(0, .2, n), 10.75 + rng.normal(0, .4, n)
    d["areas"] = [{"id": f"Z{i}", "name": f"Cell {i}", "latitude": float(lat[i]), "longitude": float(lon[i]),
                   "demand": float(rng.integers(0, 500)), "outside_weight": .2, "source_id": None, "note": ""} for i in range(n)]
    roles = ["own"] * 3 + ["competitor"] * (s - 3 - candidates) + ["candidate"] * candidates
    d["sites"] = [{"id": f"L{j}", "name": f"Site {j}", "role": roles[j], "latitude": float(59.9 + rng.normal(0, .15)),
                   "longitude": float(10.75 + rng.normal(0, .3)), "attractiveness": float(rng.uniform(.5, 2)),
                   "source_id": None, "note": ""} for j in range(s)]
    if travel:
        d["parameters"][0]["distance_mode"] = "travel_minutes"
        d["distances"] = [{"area_id": a["id"], "site_id": site["id"], "value": float(rng.uniform(1, 60))}
                          for a in d["areas"] for site in d["sites"]]
    return model.validate(d)


@pytest.fixture(scope="module")
def case():
    return large_case()


def test_large_case_conserves_demand_and_shortens_only_the_pair_table(case):
    r = model.allocate(case)
    assert r["sites"].allocated_demand.sum() == pytest.approx(r["total_demand"], rel=1e-12)
    assert len(r["areas"]) == AREAS and r["area_count"] == AREAS
    shares = r["areas"].own_share + r["areas"].outside_share
    assert ((shares > 0) & (shares <= 1 + 1e-12)).all()
    assert r["allocation_areas"] < AREAS and len(r["allocation"]) <= model.DETAIL_LIMIT
    per_area = r["allocation"].groupby("area_id").choice_share.sum()
    assert np.allclose(per_area, 1)


def test_one_pass_comparison_matches_scenario_by_scenario_allocation(case):
    comparison = model.compare(case).set_index("candidate")
    base = model.allocate(case)
    for site in [s for s in case["sites"] if s["role"] == "candidate"]:
        new = model.allocate(case, site["id"])
        row = comparison.loc[site["name"]]
        assert row.own_portfolio_change == pytest.approx(new["own_demand"] - base["own_demand"], rel=1e-9)
        assert row.outside_change == pytest.approx(new["outside_demand"] - base["outside_demand"], rel=1e-9)
        assert row.access_gap_change == pytest.approx(new["beyond_access_demand"] - base["beyond_access_demand"], abs=1e-6)
        moved = row.candidate_demand + row.existing_own_change + row.competitor_change + row.outside_change
        assert moved == pytest.approx(0, abs=1e-6 * base["total_demand"])
    sensitivity = model.sensitivity(case)
    assert len(sensitivity) == len(model.SENSITIVITY_BETAS) * CANDIDATES
    at_beta = sensitivity[sensitivity.distance_decay == case["parameters"][0]["beta"]].set_index("candidate")
    assert np.allclose(at_beta.own_portfolio_change, comparison.own_portfolio_change)


def test_travel_time_matrix_at_scale_matches_and_gaps_are_counted():
    d = large_case(n=2_000, s=10, candidates=2, travel=True)
    comparison = model.compare(d).set_index("candidate")
    base = model.allocate(d)
    new = model.allocate(d, "L9")
    assert comparison.loc["Site 9"].own_portfolio_change == pytest.approx(new["own_demand"] - base["own_demand"], rel=1e-9)
    d["distances"] = [r for r in d["distances"] if r["site_id"] != "L0"]
    count, lines = model.readiness_summary(d, limit=5)
    assert count == 2_000 and len(lines) == 5 and lines[0] == "Z0 → L0: travel minutes"
    with pytest.raises(io.DataProblem, match="and 1,988 more"):
        model.allocate(d)


def test_fast_validation_reports_the_failing_row_and_enforces_size_limits(case):
    bad = {**case, "areas": [dict(a) for a in case["areas"]]}
    bad["areas"][12_345]["demand"] = -1
    with pytest.raises(io.DataProblem, match="areas / 12345 / demand"):
        model.validate(bad)
    bad["areas"][12_345]["demand"] = True
    with pytest.raises(io.DataProblem, match="not a number"):
        model.validate(bad)
    bad["areas"][12_345].update(demand=1.0, id="1bad")
    with pytest.raises(io.DataProblem, match="areas / 12345 / id"):
        model.validate(bad)
    huge = {**case, "areas": case["areas"] * (model.MAX_PAIRS // (AREAS * SITES) + 1)}
    huge["areas"] = [{**a, "id": f"A{i}"} for i, a in enumerate(huge["areas"])]
    with pytest.raises(io.DataProblem, match="Aggregate small areas"):
        model.validate(huge)


def test_map_grid_keeps_total_demand(case):
    r = model.allocate(case)
    x, y = model.local_xy(case["areas"])
    grid, size = model.grid_aggregate(x, y, r["areas"].demand, r["areas"].own_share)
    assert 0 < len(grid) < AREAS and size > 0
    assert grid.weight.sum() == pytest.approx(r["areas"].demand.sum())
    assert grid.areas.sum() == AREAS
    assert ((grid.value >= 0) & (grid.value <= 1)).all()


def test_large_csv_upload_maps_and_builds(case):
    areas = pd.DataFrame([{"Area name": a["name"], "Latitude": a["latitude"], "Longitude": a["longitude"], "Demand": a["demand"],
                           "Outside-option weight": a["outside_weight"]} for a in case["areas"]])
    sites = pd.DataFrame([{"Location name": s["name"], "Location type": s["role"].title(), "Latitude": s["latitude"],
                           "Longitude": s["longitude"], "Site attractiveness": s["attractiveness"]} for s in case["sites"]])
    tables = sheets.load_tables([("areas.csv", areas.to_csv(index=False).encode()), ("sites.csv", sites.to_csv(index=False).encode())])
    mapped = {}
    for key, spec in fmt.QUICK.items():
        frame = tables[key]
        mapping = {f: sheets.suggest(list(frame), [t, f] + aliases) for f, (t, _, aliases) in spec["fields"].items()}
        mapped[key] = sheets.mapped_rows(frame, mapping, spec["fields"], table=spec["title"])
    settings = {"demand_unit": "Residents", "period": "2026", "attractiveness_definition": "Index", "alpha": 1.0, "beta": 1.5,
                "distance_floor": .25, "access_threshold": 5.0}
    d = fmt.build("Large upload", mapped, settings, "areas.csv, sites.csv")
    assert len(d["areas"]) == AREAS
    assert model.allocate(d)["total_demand"] == pytest.approx(model.allocate(case)["total_demand"])


def test_printable_brief_shortens_long_tables(case):
    p = io.accept(io.project("reach", case), "Tester", "Synthetic large case")
    html = model.printable(p)
    assert f"first {model.REPORT_ROWS:,} of {AREAS:,} rows" in html
    assert html.count("<tr>") < 5 * model.REPORT_ROWS


def test_streamed_excel_export_keeps_formula_text_literal(monkeypatch):
    monkeypatch.setattr(sheets, "STYLE_CELLS", 10)
    d = model.demo()["data"]
    d["sources"][0]["note"] = '=HYPERLINK("https://example.org","test")'
    raw = sheets.project_workbook(model, d)
    book = load_workbook(BytesIO(raw), data_only=False)
    assert all(cell.data_type != "f" for row in book["Sources"] for cell in row)
    assert book["Sources"]["A1"].font.b
    tables = sheets.load_tables([("export.xlsx", raw)])
    assert tables["Sources"].iloc[0]["Notes"] == d["sources"][0]["note"]
    assert len(tables["Customer areas"]) == len(d["areas"])
