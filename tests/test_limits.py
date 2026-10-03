"""Data limits (APP_CONTRACT section 9): none locally, hard caps only on a public demo (SIGNAL_PUBLIC=1)."""
from io import BytesIO
import json
from zipfile import ZipFile

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from reachsignal import limits, model, portable as io, spreadsheets as sheets
from test_scale import large_case

RENDER = "from reachsignal.ui import render\n\nrender()\n"
CAP = limits.DEMO


@pytest.fixture(scope="module")
def beyond_caps():
    """More areas, locations and area x location pairs than the public demo allows."""
    return large_case(n=CAP["areas"] + 1, s=CAP["sites"] + 1, candidates=3)


@pytest.fixture(scope="module")
def long_csv():
    rows = CAP["rows"] + 1
    return pd.DataFrame({"Area name": [f"A{i}" for i in range(rows)], "Demand": 1}).to_csv(index=False).encode()


def test_local_mode_accepts_input_beyond_the_demo_caps(monkeypatch, beyond_caps, long_csv):
    monkeypatch.delenv("SIGNAL_PUBLIC", raising=False)
    assert limits.cap("areas") is None
    assert len(beyond_caps["areas"]) * len(beyond_caps["sites"]) > CAP["pairs"]
    d = model.validate(beyond_caps)
    result = model.allocate(d)
    assert result["sites"].allocated_demand.sum() == pytest.approx(result["total_demand"], rel=1e-12)
    assert len(model.compare(d)) == 3
    assert len(sheets.load_tables([("areas.csv", long_csv)])["areas"]) == CAP["rows"] + 1
    monkeypatch.setitem(limits.DEMO, "json_mb", 0.0001)
    assert io.parse(json.dumps({"brief": "x" * 1000}))["brief"]


def test_public_demo_enforces_its_caps(monkeypatch, beyond_caps, long_csv):
    monkeypatch.setenv("SIGNAL_PUBLIC", "1")
    with pytest.raises(io.DataProblem, match="limit of the public demo"):
        model.validate(beyond_caps)
    pairs = {**beyond_caps, "areas": beyond_caps["areas"][:CAP["pairs"] // CAP["sites"] + 1],
             "sites": beyond_caps["sites"][:CAP["sites"]]}
    with pytest.raises(io.DataProblem, match="pairs.*public demo"):
        model.validate(pairs)
    with pytest.raises(io.DataProblem, match="rows.*public demo"):
        sheets.load_tables([("areas.csv", long_csv)])
    monkeypatch.setitem(limits.DEMO, "upload_mb", 0.0001)
    with pytest.raises(io.DataProblem, match="MB.*public demo"):
        sheets.load_tables([("small.csv", b"a,b\n1,2\n" * 100)])
    monkeypatch.setitem(limits.DEMO, "json_mb", 0.0001)
    with pytest.raises(io.DataProblem, match="JSON.*public demo"):
        io.parse(json.dumps({"brief": "x" * 1000}))
    assert model.validate(model.demo()["data"])  # the fictional demo fits


def test_public_demo_says_so_in_the_upload_page(monkeypatch):
    monkeypatch.setenv("SIGNAL_PUBLIC", "1")
    app = AppTest.from_string(RENDER, default_timeout=120).run()
    app.sidebar.radio(key="reach:page").set_value("1 · Add your data").run()
    assert any("Public demo limits" in str(c.value) for c in app.caption)
    monkeypatch.delenv("SIGNAL_PUBLIC")
    app.run()
    assert any("No data limits" in str(c.value) for c in app.caption)


def test_out_of_memory_is_a_plain_message(monkeypatch):
    def no_memory(*args, **kwargs):
        raise MemoryError

    monkeypatch.setattr(model, "allocate", no_memory)
    app = AppTest.from_string(RENDER, default_timeout=120).run()
    app.sidebar.radio(key="reach:page").set_value("3 · Catchment map").run()
    assert not app.exception
    assert any("not enough memory" in str(e.value) for e in app.error)


def test_zip_holds_every_pair_row_and_excel_continues_long_tables(monkeypatch):
    d = large_case(n=3_000, s=40, candidates=2)
    p = io.accept(io.project("reach", d), "Tester", "Synthetic")
    from reachsignal.ui.app import export_streams, export_tables

    tables, notes = export_tables(p)
    assert notes and len(tables["baseline_allocation"]) <= model.DETAIL_LIMIT
    raw = io.bundle(p, "<html></html>", tables, model.REFERENCES, export_streams(p))
    with ZipFile(BytesIO(raw)) as z:
        pairs = pd.read_csv(z.open("baseline_allocation.csv"), encoding="utf-8-sig")
    assert len(pairs) == 3_000 * (38 + 1)
    assert pairs.groupby("area_id").choice_share.sum().round(9).eq(1).all()
    assert pairs.allocated_demand.sum() == pytest.approx(model.allocate(d)["total_demand"])
    monkeypatch.setattr(sheets, "EXCEL_ROWS", 1_000)
    book = sheets.project_workbook(model, d)
    titles = list(sheets.load_tables.__globals__["load_workbook"](BytesIO(book), read_only=True).sheetnames)
    assert "Customer areas (cont. 3)" in titles
    back = sheets.load_tables([("export.xlsx", book)])
    assert len(back["Customer areas"]) == 3_000
    assert not any("(cont." in t for t in back)
