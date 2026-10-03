"""Huff allocation scenarios, explicit outside option and distance-based access."""
from copy import deepcopy

import numpy as np
import pandas as pd

from reachsignal import portable as io

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
                 "parameters":io.array(PARAMS,1,1),"areas":io.array(AREA,250,1),"sites":io.array(SITE,40,1),
                 "distances":io.array(DISTANCE,10000),"sources":io.array(io.SOURCE,100)})
TITLES = {"context":"Demand unit, period and common definition of attractiveness", "parameters":"Model settings · distances use km or supplied travel minutes",
          "areas":"Customer areas · demand and outside-option weight", "sites":"Existing locations and candidate alternatives",
          "distances":"Optional road/transit travel matrix · minutes from each area to each site", "sources":"Sources or input justifications"}
REFERENCES = [("Huff (1964). Defining and Estimating a Trading Area.","https://doi.org/10.1177/002224296402800307"),
              ("Esri. How Huff Model works.","https://doc.esri.com/en/arcgis-pro/latest/tool-reference/business-analyst/understanding-huff-model.html"),
              ("Esri. Create and calibrate a Huff model.","https://doc.esri.com/en/arcgis-pro/latest/help/analysis/business-analyst/huff-model-overview.html")]
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
          "Candidates are alternatives evaluated one at a time. Opening several simultaneously requires a new scenario with those locations explicitly represented.",
          "Reach adds geography and location access. Shift Signal evaluates product-launch demand movement using a different evidence design."]
AI_RULES = ("Research or structure site and area records with sources. Never invent coordinates, population, demand, site attractiveness, travel times or outside-option weights. "
            "Use null when those inputs are unsupported. Demand must have one explicitly stated unit and period; population alone is not visits or spending. "
            "Attractiveness must use one comparable positive measure across all sites. Roles are own, competitor or candidate. "
            "Keep user-supplied model settings; explain they are assumptions, not fitted parameters. For travel_minutes include every area × site pair; never substitute straight distance for travel time. "
            "For unknown locations keep both latitude and longitude null. Source notes should distinguish measured facts from planning assumptions.")
REVIEW_GUIDANCE = "Check the location coordinates, area boundaries, demand unit, attractiveness definition, transport mode and outside-option assumptions. Verify that a travel-time matrix uses the same mode and time period throughout."


def validate(data):
    d=io.validate_schema(data,SCHEMA)
    areas,sites,sources=[io.unique(d[k]) for k in ["areas","sites","sources"]]
    if "OUTSIDE" in sites:
        raise io.DataProblem("OUTSIDE is reserved for the unlisted-alternatives row. Choose another site ID.")
    if not any(s["role"]!="candidate" for s in d["sites"]):
        raise io.DataProblem("Include at least one existing own or competitor location for the baseline.")
    for row in d["areas"]+d["sites"]:
        if (row["latitude"] is None)!=(row["longitude"] is None):
            raise io.DataProblem("Supply both coordinates, or leave both null.")
        if row["source_id"] and row["source_id"] not in sources:
            raise io.DataProblem("A site or area refers to a missing source.")
    seen=set()
    for row in d["distances"]:
        key=(row["area_id"],row["site_id"])
        if key in seen or key[0] not in areas or key[1] not in sites:
            raise io.DataProblem("Travel matrix has a duplicate pair or a missing area/site reference.")
        seen.add(key)
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


def readiness(d,candidate=None):
    sites=active_sites(d,candidate)
    missing=[]
    for area in d["areas"]:
        for key in ["demand","outside_weight"]:
            if area[key] is None:
                missing.append(area["id"]+": "+key)
    for site in sites:
        if site["attractiveness"] is None:
            missing.append(site["id"]+": attractiveness")
    if d["parameters"][0]["distance_mode"]=="straight_km":
        for row in d["areas"]+sites:
            if row["latitude"] is None or row["longitude"] is None:
                missing.append(row["id"]+": coordinates")
    else:
        lookup={(r["area_id"],r["site_id"]):r["value"] for r in d["distances"]}
        for area in d["areas"]:
            for site in sites:
                if lookup.get((area["id"],site["id"])) is None:
                    missing.append(area["id"]+" → "+site["id"]+": travel minutes")
    return missing


def haversine(lat1,lon1,lat2,lon2):
    a,b=np.radians(lat1),np.radians(lat2)
    dl=np.radians(np.asarray(lon2)-np.asarray(lon1))
    v=np.sin((b-a)/2)**2+np.cos(a)*np.cos(b)*np.sin(dl/2)**2
    return 6371.0088*2*np.arcsin(np.sqrt(np.clip(v,0,1)))


def allocate(d,candidate=None):
    d=validate(d)
    missing=readiness(d,candidate)
    if missing:
        raise io.DataProblem("Complete inputs before modeling: "+"; ".join(missing[:12]))
    sites=active_sites(d,candidate)
    areas=d["areas"]
    p=d["parameters"][0]
    if p["distance_mode"]=="straight_km":
        dist=haversine(np.array([a["latitude"] for a in areas])[:,None],np.array([a["longitude"] for a in areas])[:,None],
                       np.array([s["latitude"] for s in sites])[None,:],np.array([s["longitude"] for s in sites])[None,:])
    else:
        lookup={(r["area_id"],r["site_id"]):r["value"] for r in d["distances"]}
        dist=np.array([[lookup[(a["id"],s["id"])] for s in sites] for a in areas],dtype=float)
    logw=p["alpha"]*np.log([s["attractiveness"] for s in sites])[None,:]-p["beta"]*np.log(np.maximum(dist,p["distance_floor"]))
    outside=np.array([a["outside_weight"] for a in areas],dtype=float)
    logoutside=np.full(outside.shape,-np.inf)
    np.log(outside,out=logoutside,where=outside>0)
    weights=np.column_stack([logw,logoutside])
    scaled=np.exp(weights-np.max(weights,axis=1,keepdims=True))
    probabilities=scaled/scaled.sum(axis=1,keepdims=True)
    demand=np.array([a["demand"] for a in areas],dtype=float)
    allocated=demand[:,None]*probabilities
    own=np.array([s["role"] in {"own","candidate"} for s in sites])
    nearest=dist.min(axis=1)
    nearestown=dist[:,own].min(axis=1) if own.any() else np.full(len(areas),np.nan)
    rows=[]
    for i,a in enumerate(areas):
        rows.append({"area_id":a["id"],"area":a["name"],"demand":a["demand"],"own_share":float(probabilities[i,:-1][own].sum()),
                     "outside_share":float(probabilities[i,-1]),"nearest_any":float(nearest[i]),"nearest_own":float(nearestown[i]) if own.any() else None,
                     "beyond_access_threshold":bool(nearest[i]>p["access_threshold"]),"beyond_own_threshold":bool(nearestown[i]>p["access_threshold"]) if own.any() else True})
    site_rows=[{"site_id":s["id"],"site":s["name"],"role":s["role"],"allocated_demand":float(allocated[:,j].sum())} for j,s in enumerate(sites)]
    site_rows.append({"site_id":"OUTSIDE","site":"Outside listed sites / no visit","role":"outside","allocated_demand":float(allocated[:,-1].sum())})
    detail=[{"area_id":a["id"],"site_id":s["id"],"distance":float(dist[i,j]),"distance_used":float(max(dist[i,j],p["distance_floor"])),
             "choice_share":float(probabilities[i,j]),"allocated_demand":float(allocated[i,j])} for i,a in enumerate(areas) for j,s in enumerate(sites)]
    detail += [{"area_id":a["id"],"site_id":"OUTSIDE","distance":None,"distance_used":None,"choice_share":float(probabilities[i,-1]),"allocated_demand":float(allocated[i,-1])} for i,a in enumerate(areas)]
    return {"areas":pd.DataFrame(rows),"sites":pd.DataFrame(site_rows),"allocation":pd.DataFrame(detail),
            "own_demand":float(allocated[:,:-1][:,own].sum()),"outside_demand":float(allocated[:,-1].sum()),
            "total_demand":float(demand.sum()),"beyond_access_demand":float(demand[nearest>p["access_threshold"]].sum()),
            "floored_pairs":int((dist<p["distance_floor"]).sum())}


def compare(d):
    base=allocate(d)
    rows=[]
    for candidate in [s for s in d["sites"] if s["role"]=="candidate"]:
        missing=readiness(d,candidate["id"])
        if missing:
            rows.append({"candidate":candidate["name"],"status":"Missing inputs: "+"; ".join(missing[:4]),"candidate_demand":None,
                         "own_portfolio_change":None,"existing_own_change":None,"competitor_change":None,"outside_change":None,"access_gap_change":None})
            continue
        new=allocate(d,candidate["id"])
        def amount(result,role):
            return result["sites"].loc[result["sites"].role.eq(role),"allocated_demand"].sum()
        rows.append({"candidate":candidate["name"],"status":"Complete","candidate_demand":float(amount(new,"candidate")),
                     "own_portfolio_change":new["own_demand"]-base["own_demand"],"existing_own_change":float(amount(new,"own")-amount(base,"own")),
                     "competitor_change":float(amount(new,"competitor")-amount(base,"competitor")),"outside_change":new["outside_demand"]-base["outside_demand"],
                     "access_gap_change":new["beyond_access_demand"]-base["beyond_access_demand"]})
    return pd.DataFrame(rows,columns=["candidate","status","candidate_demand","own_portfolio_change","existing_own_change","competitor_change","outside_change","access_gap_change"])


def sensitivity(d):
    rows=[]
    for beta in [0.5,1.0,1.5,2.0,3.0]:
        changed=deepcopy(d)
        changed["parameters"][0]["beta"]=beta
        for row in compare(changed).to_dict("records"):
            rows.append({"distance_decay":beta,**row})
    return pd.DataFrame(rows)


def local_xy(rows):
    if not rows or any(r["latitude"] is None or r["longitude"] is None for r in rows):
        raise io.DataProblem("Coordinates are missing. Travel-time calculations still work, but a coordinate map needs both latitude and longitude.")
    lat0=float(np.mean([r["latitude"] for r in rows]))
    lon0=float(rows[0]["longitude"])
    delta=(np.array([r["longitude"] for r in rows])-lon0+180)%360-180
    return 6371.0088*np.radians(delta)*np.cos(np.radians(lat0)),6371.0088*np.radians(np.array([r["latitude"] for r in rows])-lat0)


def printable(p):
    sections=[("Model inputs",pd.DataFrame(p["data"]["parameters"])),("Demand areas",pd.DataFrame(p["data"]["areas"])),("Locations",pd.DataFrame(p["data"]["sites"]))]
    if io.reviewed(p) and not readiness(p["data"]):
        r=allocate(p["data"])
        sections += [("Baseline site allocations",r["sites"]),("Baseline access and choice",r["areas"]),("Candidate comparisons",compare(p["data"]))]
    else:
        sections.append(("Calculation status","<p>Review inputs and complete missing data before interpreting a modeled scenario.</p>"))
    return io.report("Reach Signal · location scenario brief",p,sections,REFERENCES,LIMITS)
