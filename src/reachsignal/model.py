"""Huff allocation scenarios, explicit outside option and distance-based access.

The engine works on arrays in blocks of customer areas, so memory stays bounded by the block size and the number of
areas, not by areas × locations.
"""
from types import SimpleNamespace

import numpy as np
import pandas as pd

from reachsignal import portable as io

MAX_AREAS = 500_000          # customer areas (fits one Excel sheet for the round trip)
MAX_SITES = 500              # own, competitor and candidate locations together
MAX_DISTANCES = 1_000_000    # travel-time pairs (one Excel sheet holds 1,048,575 data rows)
MAX_PAIRS = 25_000_000       # areas × locations evaluated by the model
DETAIL_LIMIT = 100_000       # rows in the pair-level allocation table
REPORT_ROWS = 200            # rows per table in the printable brief
CHUNK_CELLS = 1_000_000      # area × location cells per computation block (8 MB per float array)
ROW_TABLES = ("areas", "sites", "distances")
SIZE_ADVICE = "Aggregate small areas (for example postcodes into districts or a coarser grid), or remove locations you do not need."

REF = {"anyOf": [io.ID, {"type": "null"}]}
LAT = io.number(-85,85,True)
LON = io.number(-180,180,True)
AREA = io.obj({"id":io.ID,"name":io.text(150),"latitude":LAT,"longitude":LON,"demand":io.number(0,1e12,True),
               "outside_weight":io.number(0,1e12,True),"source_id":REF,"note":io.text(1000,True)})
SITE = io.obj({"id":io.ID,"name":io.text(150),"role":{"enum":["own","competitor","candidate"]},"latitude":LAT,"longitude":LON,
               "attractiveness":io.number(1e-6,1e6,True),"source_id":REF,"note":io.text(1000,True)})
DISTANCE = io.obj({"area_id":io.ID,"site_id":io.ID,"value":io.number(0,1e7,True)})
PARAMS = io.obj({"distance_mode":{"enum":["straight_km","travel_minutes"]},"alpha":io.number(.1,5),"beta":io.number(0,5),
                 "distance_floor":io.number(1e-6,10000),"access_threshold":io.number(1e-6,10000)})
SCHEMA = io.obj({"schema_version":{"const":"1.0"},"brief":io.text(2500),
                 "context":io.array(io.obj({"demand_unit":io.text(150),"period":io.text(150),"attractiveness_definition":io.text(800)}),1,1),
                 "parameters":io.array(PARAMS,1,1),"areas":io.array(AREA,MAX_AREAS,1),"sites":io.array(SITE,MAX_SITES,1),
                 "distances":io.array(DISTANCE,MAX_DISTANCES),"sources":io.array(io.SOURCE,100)})
TITLES = {"context":"Demand unit, period and common definition of attractiveness", "parameters":"Model settings · distances use km or supplied travel minutes",
          "areas":"Customer areas · demand and outside-option weight", "sites":"Existing locations and candidate alternatives",
          "distances":"Optional road/transit travel matrix · minutes from each area to each site", "sources":"Sources or input justifications"}
REFERENCES = [("Huff, D. L. (1963). A probabilistic analysis of shopping center trade areas. Land Economics, 39(1).","https://doi.org/10.2307/3144521"),
              ("Huff, D. L. (1964). Defining and estimating a trading area. Journal of Marketing, 28(3), 34–38.","https://doi.org/10.1177/002224296402800307"),
              ("Nakanishi, M., & Cooper, L. G. (1974). Parameter estimation for a multiplicative competitive interaction model: Least squares approach. Journal of Marketing Research, 11(3), 303–311.","https://doi.org/10.1177/002224377401100309"),
              ("Esri. How Huff Model works. ArcGIS Pro documentation.","https://doc.esri.com/en/arcgis-pro/latest/tool-reference/business-analyst/understanding-huff-model.html"),
              ("Esri. Create a Huff model. ArcGIS Pro documentation.","https://doc.esri.com/en/arcgis-pro/latest/help/analysis/business-analyst/huff-model-overview.html")]
METHOD = ("Site attraction for area i and site j is H_ij = A_j^alpha / max(d_ij, floor)^beta. "
          "Modeled choice share is H_ij / (Σj H_ij + outside_i). Each area's supplied demand is allocated using these shares. "
          "The outside weight is a user-defined extension representing unlisted alternatives or no visit; it must use the same attraction scale. "
          "The baseline includes existing own and competitor sites. Each candidate is added separately, keeping total demand and other inputs fixed. "
          "Straight distances use the Haversine formula with Earth radius 6,371.0088 km. Travel-time mode uses a complete uploaded matrix of minutes. "
          "Access coverage is based on the raw nearest distance and your chosen threshold, independently of Huff probabilities.")
LIMITS = ["These are conditional location scenarios. Attractiveness, distance decay and demand need local evidence and calibration before predictive use.",
          "The app does not estimate demand, profit, actual market share, causal cannibalization, capacity or congestion. All demand stays fixed across scenarios.",
          "A zero outside weight forces all demand to the listed sites. A positive outside weight is a scenario assumption, not an estimated no-purchase rate.",
          "Outside weights share the attraction scale. Changing the distance unit, alpha or attractiveness scale also changes their relative importance; recalibrate them consistently.",
          "Customer-area centroids simplify where people actually live or travel. Straight-line km ignore roads, water, mountains and transport barriers.",
          "The offline coordinate map is a local schematic without streets or boundaries. Coverage means meeting a declared distance threshold, not observed customer satisfaction or service quality.",
          "Large cases are computed over every area. Only the map, on-screen tables, the pair-level allocation table and the printable brief aggregate or shorten what they show, and they say so.",
          "Candidates are alternatives evaluated one at a time. Opening several simultaneously requires a new scenario with those locations explicitly represented.",
          "Reach adds geography and location access. Shift Signal evaluates product-launch demand movement using a different evidence design."]
AI_RULES = ("Research or structure site and area records with sources. Never invent coordinates, population, demand, site attractiveness, travel times or outside-option weights. "
            "Use null when those inputs are unsupported. Demand must have one explicitly stated unit and period; population alone is not visits or spending. "
            "Attractiveness must use one comparable positive measure across all sites. Roles are own, competitor or candidate. "
            "Keep user-supplied model settings; explain they are assumptions, not fitted parameters. For travel_minutes include every area × site pair; never substitute straight distance for travel time. "
            "For unknown locations keep both latitude and longitude null. Source notes should distinguish measured facts from planning assumptions.")
REVIEW_GUIDANCE = "Check the location coordinates, area boundaries, demand unit, attractiveness definition, transport mode and outside-option assumptions. Verify that a travel-time matrix uses the same mode and time period throughout."



SHELL = {**SCHEMA, "properties": {**SCHEMA["properties"], **{name: {"type": "array"} for name in ROW_TABLES}}}


def validate(data):
    """Check a case. The row tables are checked column by column (fast for large cases), the rest with jsonschema."""
    if not isinstance(data, dict):
        raise io.DataProblem("The model input must be one JSON object.")
    shell = io.validate_schema({k: [] if k in ROW_TABLES and isinstance(v, list) else v for k, v in data.items()}, SHELL)
    d = dict(shell)
    for name in ROW_TABLES:
        spec = SCHEMA["properties"][name]
        rows = data[name]
        if len(rows) < spec.get("minItems", 0):
            raise io.DataProblem(f"{name}: include at least {spec['minItems']} row.")
        if len(rows) > spec["maxItems"]:
            raise io.DataProblem(f"{name}: at most {spec['maxItems']:,} rows are supported; this case has {len(rows):,}. {SIZE_ADVICE}")
        d[name] = io.validate_rows(rows, spec["items"], name)
    areas,sites,sources=[io.unique(d[k]) for k in ["areas","sites","sources"]]
    if "OUTSIDE" in sites:
        raise io.DataProblem("OUTSIDE is reserved for the unlisted-alternatives row. Choose another site ID.")
    if not any(s["role"]!="candidate" for s in d["sites"]):
        raise io.DataProblem("Include at least one existing own or competitor location for the baseline.")
    pairs = len(d["areas"]) * len(d["sites"])
    if pairs > MAX_PAIRS:
        raise io.DataProblem(f"The model compares every customer area with every location: {len(d['areas']):,} areas × "
                             f"{len(d['sites']):,} locations = {pairs:,} pairs, above the {MAX_PAIRS:,} supported. {SIZE_ADVICE}")
    for row in d["areas"]+d["sites"]:
        if (row["latitude"] is None)!=(row["longitude"] is None):
            raise io.DataProblem("Supply both coordinates, or leave both null.")
        if row["source_id"] and row["source_id"] not in sources:
            raise io.DataProblem("A site or area refers to a missing source.")
    if d["distances"]:
        frame = pd.DataFrame({"a": [r["area_id"] for r in d["distances"]], "s": [r["site_id"] for r in d["distances"]]})
        if frame.duplicated().any() or not frame.a.isin(list(areas)).all() or not frame.s.isin(list(sites)).all():
            raise io.DataProblem("Travel matrix has a duplicate pair or a missing area/site reference.")
    return d


def starter(brief):
    return {"schema_version":"1.0","brief":brief,"context":[{"demand_unit":"Specify comparable demand units","period":"Specify period","attractiveness_definition":"Define one common site attractiveness measure"}],
            "parameters":[{"distance_mode":"straight_km","alpha":1.0,"beta":1.5,"distance_floor":.25,"access_threshold":5.0}],
            "areas":[{"id":"Z1","name":"Customer area","latitude":None,"longitude":None,"demand":None,"outside_weight":None,"source_id":None,"note":""}],
            "sites":[{"id":"L1","name":"Existing location","role":"own","latitude":None,"longitude":None,"attractiveness":None,"source_id":None,"note":""}],
            "distances":[],"sources":[]}


def demo():
    d=starter("FICTIONAL DEMO: compare two alternative café locations around an illustrative Oslo catchment. All locations and demand inputs are invented.")
    d["context"]=[{"demand_unit":"Potential café visits per month","period":"Illustrative planning month","attractiveness_definition":"Relative café attraction index; existing own site = 1. These are assumed values."}]
    d["sources"]=[{"id":"N1","title":"Fictional spatial planning case","url":None,"note":"Synthetic coordinates near Oslo and invented demand. No real business, official population data or measured travel times."}]
    zones=[("West",59.920,10.680,1200),("Northwest",59.960,10.700,900),("North",59.975,10.750,1300),
           ("Northeast",59.960,10.815,950),("East",59.930,10.845,1400),("Centre",59.915,10.750,2100),
           ("South",59.875,10.785,1050),("Outer east",59.905,10.925,1250)]
    d["areas"]=[{"id":f"Z{i}","name":name,"latitude":lat,"longitude":lon,"demand":demand,"outside_weight":.15,"source_id":"N1","note":"Synthetic area centroid and demand."} for i,(name,lat,lon,demand) in enumerate(zones,1)]
    sites=[("L1","Existing centre café","own",59.915,10.740,1), ("L2","West competitor","competitor",59.930,10.690,1.2),
           ("L3","East competitor","competitor",59.930,10.820,1.1), ("C1","North candidate","candidate",59.966,10.752,.9),
           ("C2","Outer-east candidate","candidate",59.906,10.915,.9)]
    d["sites"]=[{"id":sid,"name":name,"role":role,"latitude":lat,"longitude":lon,"attractiveness":a,"source_id":"N1","note":"Fictional site and assumed attraction."} for sid,name,role,lat,lon,a in sites]
    return io.accept(io.project("reach",validate(d),"FICTIONAL DEMO — synthetic geography and assumed demand"),"Fictional reviewer","Checked example model structure; no real-world inputs were verified.")


def active_sites(d,candidate=None):
    if candidate is not None and candidate not in {s["id"] for s in d["sites"] if s["role"]=="candidate"}:
        raise io.DataProblem("Choose an existing candidate ID.")
    return [s for s in d["sites"] if s["role"]!="candidate" or s["id"]==candidate]


def _column(rows, key):
    return np.array([np.nan if r[key] is None else r[key] for r in rows], dtype=float)


def _blocks(n, width):
    step = max(1, CHUNK_CELLS // max(1, width))
    for start in range(0, n, step):
        yield start, min(n, start + step)


class _Geometry:
    """Raw distances from customer areas to locations, delivered one block of areas at a time."""

    def __init__(self, d):
        self.straight = d["parameters"][0]["distance_mode"] == "straight_km"
        self.n = len(d["areas"])
        if self.straight:
            self.alat, self.alon = _column(d["areas"], "latitude"), _column(d["areas"], "longitude")
            self.slat, self.slon = _column(d["sites"], "latitude"), _column(d["sites"], "longitude")
            return
        area_index = {a["id"]: i for i, a in enumerate(d["areas"])}
        site_index = {s["id"]: j for j, s in enumerate(d["sites"])}
        rows = [r for r in d["distances"] if r["value"] is not None]
        a = np.fromiter((area_index[r["area_id"]] for r in rows), dtype=np.int64, count=len(rows))
        s = np.fromiter((site_index[r["site_id"]] for r in rows), dtype=np.int64, count=len(rows))
        present = np.unique(s)
        self.column = np.full(len(d["sites"]), -1, dtype=np.int64)
        self.column[present] = np.arange(len(present))
        self.matrix = np.full((self.n, len(present)), np.nan)
        self.matrix[a, self.column[s]] = [r["value"] for r in rows]

    def block(self, start, stop, cols):
        cols = np.asarray(cols, dtype=np.int64)
        if self.straight:
            return haversine(self.alat[start:stop, None], self.alon[start:stop, None], self.slat[None, cols], self.slon[None, cols])
        mapped = self.column[cols]
        out = np.full((stop - start, len(cols)), np.nan)
        known = mapped >= 0
        out[:, known] = self.matrix[start:stop][:, mapped[known]]
        return out


def readiness_summary(d, candidate=None, limit=1000):
    """(number of missing inputs, the first `limit` of them as readable lines) for the baseline or one candidate."""
    sites = active_sites(d, candidate)
    count, lines = 0, []

    def add(text):
        nonlocal count
        count += 1
        if len(lines) < limit:
            lines.append(text)

    for area in d["areas"]:
        for key in ["demand","outside_weight"]:
            if area[key] is None:
                add(area["id"]+": "+key)
    for site in sites:
        if site["attractiveness"] is None:
            add(site["id"]+": attractiveness")
    if d["parameters"][0]["distance_mode"]=="straight_km":
        for rows in (d["areas"], sites):
            for row in rows:
                if row["latitude"] is None or row["longitude"] is None:
                    add(row["id"]+": coordinates")
        return count, lines
    geo = _Geometry(d)
    index = {s["id"]: j for j, s in enumerate(d["sites"])}
    cols = [index[s["id"]] for s in sites]
    for start, stop in _blocks(len(d["areas"]), len(cols)):
        gap = np.isnan(geo.block(start, stop, cols))
        total = int(gap.sum())
        if not total:
            continue
        room = max(0, limit - len(lines))
        for i, j in np.argwhere(gap)[:room]:
            lines.append(d["areas"][start + i]["id"]+" → "+sites[j]["id"]+": travel minutes")
        count += total
    return count, lines


def readiness(d,candidate=None):
    """Readable list of missing inputs (at most 1,000 lines; use readiness_summary for the full count)."""
    return readiness_summary(d, candidate)[1]


def _require_complete(d, candidate=None):
    count, missing = readiness_summary(d, candidate, 12)
    if count:
        more = f"; and {count - len(missing):,} more" if count > len(missing) else ""
        raise io.DataProblem("Complete inputs before modeling: "+"; ".join(missing)+more)


def haversine(lat1,lon1,lat2,lon2):
    a,b=np.radians(lat1),np.radians(lat2)
    dl=np.radians(np.asarray(lon2)-np.asarray(lon1))
    v=np.sin((b-a)/2)**2+np.cos(a)*np.cos(b)*np.sin(dl/2)**2
    return 6371.0088*2*np.arcsin(np.sqrt(np.clip(v,0,1)))


def _log_outside(outside):
    out = np.full(outside.shape, -np.inf)
    np.log(outside, out=out, where=outside > 0)
    return out


def _prepare(d):
    sites = d["sites"]
    return SimpleNamespace(p=d["parameters"][0], n=len(d["areas"]), demand=_column(d["areas"], "demand"),
                           outside=_column(d["areas"], "outside_weight"), attract=_column(sites, "attractiveness"),
                           role=np.array([s["role"] for s in sites]), geo=_Geometry(d))


def allocate(d,candidate=None):
    d=validate(d)
    _require_complete(d, candidate)
    sites=active_sites(d,candidate)
    areas=d["areas"]
    P=_prepare(d)
    p=P.p
    n,m=P.n,len(sites)
    cols=[j for j,s in enumerate(d["sites"]) if s["role"]!="candidate" or s["id"]==candidate]
    own=np.isin(P.role[cols],["own","candidate"])
    loga=p["alpha"]*np.log(P.attract[cols])
    own_share,outside_share,nearest,nearest_own=(np.empty(n) for _ in range(4))
    site_alloc=np.zeros(m)
    outside_alloc=0.0
    floored=0
    shown=n if n*(m+1)<=DETAIL_LIMIT else max(1,DETAIL_LIMIT//(m+1))
    detail_dist,detail_prob=[],[]
    for start,stop in _blocks(n,m):
        dist=P.geo.block(start,stop,cols)
        floored+=int((dist<p["distance_floor"]).sum())
        nearest[start:stop]=dist.min(axis=1)
        if own.any():
            nearest_own[start:stop]=dist[:,own].min(axis=1)
        if start<shown:
            detail_dist.append(dist[:shown-start].copy())
        w=np.maximum(dist,p["distance_floor"])
        np.log(w,out=w)
        w*=-p["beta"]
        w+=loga
        lo=_log_outside(P.outside[start:stop])
        top=np.maximum(w.max(axis=1),lo)
        w-=top[:,None]
        np.exp(w,out=w)
        so=np.exp(lo-top)
        denom=w.sum(axis=1)+so
        own_share[start:stop]=w[:,own].sum(axis=1)/denom
        outside_share[start:stop]=so/denom
        scale=P.demand[start:stop]/denom
        site_alloc+=scale@w
        outside_alloc+=float(scale@so)
        if start<shown:
            detail_prob.append(w[:shown-start]/denom[:shown-start,None])
    threshold=p["access_threshold"]
    frame=pd.DataFrame({"area_id":[a["id"] for a in areas],"area":[a["name"] for a in areas],"demand":P.demand,
                        "own_share":own_share,"outside_share":outside_share,"nearest_any":nearest,
                        "nearest_own":nearest_own if own.any() else [None]*n,
                        "beyond_access_threshold":nearest>threshold,
                        "beyond_own_threshold":nearest_own>threshold if own.any() else np.ones(n,dtype=bool)})
    site_rows=[{"site_id":s["id"],"site":s["name"],"role":s["role"],"allocated_demand":float(site_alloc[j])} for j,s in enumerate(sites)]
    site_rows.append({"site_id":"OUTSIDE","site":"Outside listed sites / no visit","role":"outside","allocated_demand":outside_alloc})
    raw=np.concatenate(detail_dist)
    prob=np.concatenate(detail_prob)
    ids=np.array([a["id"] for a in areas[:shown]],dtype=object)
    blank=np.full(shown,np.nan)
    detail=pd.DataFrame({"area_id":np.concatenate([np.repeat(ids,m),ids]),
                         "site_id":np.concatenate([np.tile(np.array([s["id"] for s in sites],dtype=object),shown),np.full(shown,"OUTSIDE",dtype=object)]),
                         "distance":np.concatenate([raw.ravel(),blank]),
                         "distance_used":np.concatenate([np.maximum(raw,p["distance_floor"]).ravel(),blank]),
                         "choice_share":np.concatenate([prob.ravel(),outside_share[:shown]]),
                         "allocated_demand":np.concatenate([(prob*P.demand[:shown,None]).ravel(),outside_share[:shown]*P.demand[:shown]])})
    return {"areas":frame,"sites":pd.DataFrame(site_rows),"allocation":detail,
            "own_demand":float(site_alloc[own].sum()),"outside_demand":outside_alloc,
            "total_demand":float(P.demand.sum()),"beyond_access_demand":float(P.demand[nearest>threshold].sum()),
            "floored_pairs":floored,"allocation_areas":shown,"area_count":n}


COMPARE_COLUMNS = ["candidate","status","candidate_demand","own_portfolio_change","existing_own_change","competitor_change","outside_change","access_gap_change"]


def _candidate_gaps(d, site, geo, j, limit=4):
    """Inputs a complete baseline still lacks for one candidate (the candidate-specific part of readiness)."""
    lines = []
    if site["attractiveness"] is None:
        lines.append(site["id"]+": attractiveness")
    if d["parameters"][0]["distance_mode"]=="straight_km":
        if site["latitude"] is None or site["longitude"] is None:
            lines.append(site["id"]+": coordinates")
    else:
        gap = np.isnan(geo.block(0, geo.n, [j])[:, 0])
        lines += [d["areas"][i]["id"]+" → "+site["id"]+": travel minutes" for i in np.flatnonzero(gap)[:limit]]
    return lines[:limit]


def _comparisons(d, betas):
    """Candidate comparisons for several distance-decay values in one pass over the areas.

    Adding candidate c to the baseline only adds H_ic to each area's denominator, so once the baseline sums per area
    are known, every candidate's reallocation follows without recomputing the other sites."""
    d=validate(d)
    _require_complete(d)
    P=_prepare(d)
    p=P.p
    base=[j for j,s in enumerate(d["sites"]) if s["role"]!="candidate"]
    status={}
    ready=[]
    for j,s in enumerate(d["sites"]):
        if s["role"]=="candidate":
            gaps=_candidate_gaps(d,s,P.geo,j)
            status[j]="Missing inputs: "+"; ".join(gaps) if gaps else "Complete"
            if not gaps:
                ready.append(j)
    cols=base+ready
    nb,c=len(base),len(ready)
    own_b,comp_b=P.role[base]=="own",P.role[base]=="competitor"
    loga=p["alpha"]*np.log(P.attract[cols])
    threshold=p["access_threshold"]
    sums={beta:{**{k:np.zeros(c) for k in ["cand","own","comp","out"]},**{k:0.0 for k in ["base_own","base_comp","base_out"]}} for beta in betas}
    base_beyond,beyond=0.0,np.zeros(c)
    for start,stop in _blocks(P.n,len(cols)):
        dist=P.geo.block(start,stop,cols)
        dem=P.demand[start:stop]
        far=dist[:,:nb].min(axis=1)>threshold
        base_beyond+=float(dem[far].sum())
        beyond+=dem@(far[:,None]&(dist[:,nb:]>threshold))
        logd=np.log(np.maximum(dist,p["distance_floor"]))
        lo=_log_outside(P.outside[start:stop])
        for beta in betas:
            w=loga-beta*logd
            top=np.maximum(w.max(axis=1),lo)
            w-=top[:,None]
            np.exp(w,out=w)
            so=np.exp(lo-top)
            e,h=w[:,:nb],w[:,nb:]
            total=e.sum(axis=1)+so
            own,comp=e[:,own_b].sum(axis=1),e[:,comp_b].sum(axis=1)
            acc=sums[beta]
            acc["base_own"]+=float(dem@(own/total))
            acc["base_comp"]+=float(dem@(comp/total))
            acc["base_out"]+=float(dem@(so/total))
            if c:
                inv=1.0/(total[:,None]+h)
                acc["cand"]+=dem@(h*inv)
                acc["own"]+=(dem*own)@inv
                acc["comp"]+=(dem*comp)@inv
                acc["out"]+=(dem*so)@inv
    result={}
    for beta in betas:
        acc=sums[beta]
        rows=[]
        for j,s in enumerate(d["sites"]):
            if s["role"]!="candidate":
                continue
            if status[j]!="Complete":
                rows.append({"candidate":s["name"],"status":status[j],**{k:None for k in COMPARE_COLUMNS[2:]}})
                continue
            i=ready.index(j)
            rows.append({"candidate":s["name"],"status":"Complete","candidate_demand":float(acc["cand"][i]),
                         "own_portfolio_change":float(acc["own"][i]+acc["cand"][i]-acc["base_own"]),
                         "existing_own_change":float(acc["own"][i]-acc["base_own"]),
                         "competitor_change":float(acc["comp"][i]-acc["base_comp"]),
                         "outside_change":float(acc["out"][i]-acc["base_out"]),
                         "access_gap_change":float(beyond[i]-base_beyond)})
        result[beta]=pd.DataFrame(rows,columns=COMPARE_COLUMNS)
    return result


def compare(d):
    beta=d["parameters"][0]["beta"]
    return _comparisons(d,[beta])[beta]


SENSITIVITY_BETAS = [0.5,1.0,1.5,2.0,3.0]


def sensitivity(d):
    frames=[frame.assign(distance_decay=beta)[["distance_decay",*COMPARE_COLUMNS]] for beta,frame in _comparisons(d,SENSITIVITY_BETAS).items()]
    return pd.concat(frames,ignore_index=True)


def local_xy(rows):
    if not rows or any(r["latitude"] is None or r["longitude"] is None for r in rows):
        raise io.DataProblem("Coordinates are missing. Travel-time calculations still work, but a coordinate map needs both latitude and longitude.")
    lat0=float(np.mean([r["latitude"] for r in rows]))
    lon0=float(rows[0]["longitude"])
    delta=(np.array([r["longitude"] for r in rows])-lon0+180)%360-180
    return 6371.0088*np.radians(delta)*np.cos(np.radians(lat0)),6371.0088*np.radians(np.array([r["latitude"] for r in rows])-lat0)


def grid_aggregate(x, y, weight, value, cells=60):
    """Aggregate many map points into a square grid for display.

    Returns one row per occupied cell (member centroid, number of areas, summed weight and weight-averaged value, or
    a plain mean where a cell's weights are all zero) and the cell size in the units of x and y."""
    x,y,weight,value=(np.asarray(v,dtype=float) for v in (x,y,weight,value))
    size=max(float(np.ptp(x)),float(np.ptp(y)),1e-9)/cells
    ix=np.minimum(((x-x.min())/size).astype(np.int64),cells)
    iy=np.minimum(((y-y.min())/size).astype(np.int64),cells)
    _,inverse=np.unique(ix*(cells+1)+iy,return_inverse=True)
    count=np.bincount(inverse)
    wsum=np.bincount(inverse,weights=weight)
    plain=np.bincount(inverse,weights=value)/count
    weighted=np.bincount(inverse,weights=weight*value)/np.where(wsum>0,wsum,1)
    frame=pd.DataFrame({"x":np.bincount(inverse,weights=x)/count,"y":np.bincount(inverse,weights=y)/count,"areas":count,
                        "weight":wsum,"value":np.where(wsum>0,weighted,plain)})
    return frame,size


def _section(label, rows):
    total=len(rows)
    frame=pd.DataFrame(rows[:REPORT_ROWS]) if isinstance(rows,list) else rows.head(REPORT_ROWS)
    if total>REPORT_ROWS:
        label+=f" · first {REPORT_ROWS:,} of {total:,} rows (the Excel and ZIP exports hold every row)"
    return label,frame


def printable(p):
    sections=[("Model inputs",pd.DataFrame(p["data"]["parameters"])),_section("Demand areas",p["data"]["areas"]),_section("Locations",p["data"]["sites"])]
    if io.reviewed(p) and not readiness_summary(p["data"],limit=0)[0]:
        r=allocate(p["data"])
        sections += [_section("Baseline site allocations",r["sites"]),_section("Baseline access and choice",r["areas"]),_section("Candidate comparisons",compare(p["data"]))]
    else:
        sections.append(("Calculation status","<p>Review inputs and complete missing data before interpreting a modeled scenario.</p>"))
    return io.report("Reach Signal · location scenario brief",p,sections,REFERENCES,LIMITS)
