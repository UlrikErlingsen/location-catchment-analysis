from copy import deepcopy

import numpy as np
import pytest

from reachsignal import model as m,portable as io


def simple_case():
    d=m.starter("Analytical reference case")
    d["parameters"][0].update(distance_mode="travel_minutes",alpha=1,beta=1,distance_floor=.1,access_threshold=3)
    d["areas"][0].update(demand=120,outside_weight=1)
    d["sites"][0].update(attractiveness=2)
    d["sites"].append({**d["sites"][0],"id":"L2","name":"Competitor","role":"competitor","attractiveness":4})
    d["distances"]=[{"area_id":"Z1","site_id":"L1","value":2},{"area_id":"Z1","site_id":"L2","value":4}]
    return m.validate(d)


def test_hand_computed_huff_with_outside_option():
    r=m.allocate(simple_case())
    # Attractions are 2/2 = 1, 4/4 = 1, outside = 1.
    assert list(r["sites"].allocated_demand)==pytest.approx([40,40,40])
    assert r["own_demand"]==pytest.approx(40)
    assert r["total_demand"]==120
    assert r["areas"].iloc[0].nearest_any==2
    assert not r["areas"].iloc[0].beyond_access_threshold


def test_equal_sites_and_closed_set_split_demand_evenly():
    d=simple_case()
    d["areas"][0]["outside_weight"]=0
    r=m.allocate(d)
    assert list(r["sites"].allocated_demand)==pytest.approx([60,60,0])


def test_candidate_reassignment_conserves_mass_and_portfolio_identity():
    d=simple_case()
    d["sites"].append({**d["sites"][0],"id":"C1","role":"candidate","name":"New site"})
    d["distances"].append({"area_id":"Z1","site_id":"C1","value":2})
    r=m.compare(d).iloc[0]
    assert r.candidate_demand==pytest.approx(30)
    assert r.own_portfolio_change==pytest.approx(20)
    assert r.existing_own_change==pytest.approx(-10)
    assert r.competitor_change==pytest.approx(-10)
    assert r.outside_change==pytest.approx(-10)
    assert r.candidate_demand+r.existing_own_change+r.competitor_change+r.outside_change==pytest.approx(0)


def test_haversine_reference_distance_and_dateline():
    assert m.haversine(0,0,0,1)==pytest.approx(111.19508,abs=.001)
    assert m.haversine(0,179.5,0,-179.5)==pytest.approx(111.19508,abs=.001)
    assert m.haversine(60,10,60,10)==0


def test_distance_floor_is_separate_from_raw_access_distance():
    d=simple_case()
    d["distances"][0]["value"]=0
    r=m.allocate(d)
    assert r["floored_pairs"]==1
    assert r["allocation"].iloc[0].distance==0
    assert r["allocation"].iloc[0].distance_used==.1
    assert np.isfinite(r["sites"].allocated_demand).all()


def test_unknown_candidate_does_not_prevent_baseline_and_is_not_zero():
    d=m.demo()["data"]
    d["sites"][-1]["attractiveness"]=None
    assert not m.readiness(d)
    assert m.allocate(d)["total_demand"]>0
    row=m.compare(d).iloc[-1]
    assert row.status.startswith("Missing") and np.isnan(row.candidate_demand)


def test_missing_distance_does_not_become_a_straight_line_fallback():
    d=simple_case()
    d["distances"].pop()
    with pytest.raises(io.DataProblem,match="travel minutes"):
        m.allocate(d)


@pytest.mark.parametrize("mutate",[
    lambda d:d["areas"][0].update(demand=-1),
    lambda d:d["sites"][0].update(attractiveness=0),
    lambda d:d["parameters"][0].update(distance_floor=0),
    lambda d:d["areas"][0].update(latitude=91,longitude=10),
    lambda d:d["areas"][0].update(latitude=None,longitude=10),
    lambda d:d["areas"][0].update(outside_weight=float("inf")),
    lambda d:d["sites"][0].update(source_id="missing"),
    lambda d:d["distances"].append(deepcopy(d["distances"][0])),
    lambda d:d["distances"][0].update(site_id="missing"),
    lambda d:d["sites"][0].update(id="OUTSIDE"),
])
def test_invalid_models_rejected(mutate):
    d=simple_case()
    mutate(d)
    with pytest.raises(io.DataProblem):
        m.validate(d)


def test_starter_blocks_unknown_demand_and_geometry():
    d=m.validate(m.starter("Our location study"))
    assert m.readiness(d)
    with pytest.raises(io.DataProblem):
        m.allocate(d)


def test_random_models_keep_mass_and_valid_probabilities():
    rng=np.random.default_rng(481)
    for _ in range(20):
        d=simple_case()
        d["areas"][0]["demand"]=float(rng.uniform(0,10000))
        d["areas"][0]["outside_weight"]=float(rng.uniform(0,5))
        d["parameters"][0]["beta"]=float(rng.uniform(0,5))
        for site in d["sites"]:
            site["attractiveness"]=float(rng.uniform(.01,100))
        for row in d["distances"]:
            row["value"]=float(rng.uniform(0,200))
        r=m.allocate(d)
        assert r["sites"].allocated_demand.sum()==pytest.approx(r["total_demand"])
        assert r["allocation"].choice_share.sum()==pytest.approx(1)
        assert r["allocation"].choice_share.between(0,1).all()


def test_zero_demand_and_no_own_sites_remain_well_defined():
    d=simple_case()
    d["areas"][0]["demand"]=0
    d["sites"][0]["role"]="competitor"
    r=m.allocate(d)
    assert r["total_demand"]==0 and r["own_demand"]==0
    assert r["areas"].iloc[0].nearest_own is None
    assert r["areas"].iloc[0].beyond_own_threshold


def test_coordinate_map_wraps_dateline_and_missing_geometry_is_clear():
    rows=[{"latitude":0,"longitude":179.5},{"latitude":0,"longitude":-179.5}]
    x,y=m.local_xy(rows)
    assert abs(x[1]-x[0])==pytest.approx(111.19508,abs=.001)
    rows[0]["latitude"]=None
    with pytest.raises(io.DataProblem,match="Coordinates"):
        m.local_xy(rows)


def test_export_blocks_unreviewed_numbers_and_escapes_labels():
    p=m.demo()
    assert "Baseline site allocations" in m.printable(p)
    p["review"]=None
    p["data"]["sites"][0]["name"]='<script>alert("bad")</script>'
    html=m.printable(p)
    assert "<script" not in html and "&lt;script&gt;" in html
    assert "Baseline site allocations" not in html
    assert io.restore(io.json_bytes(p),"reach",m.validate)==p
