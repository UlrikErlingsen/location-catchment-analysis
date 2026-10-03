"""Friendly customer-area and location spreadsheet layouts."""
from . import model, portable as io

TABLE_NAMES = {"context": "Scope", "parameters": "Model settings", "areas": "Customer areas", "sites": "Locations", "distances": "Travel times", "sources": "Sources"}
LABELS = {"role": "Location type", "outside_weight": "Outside-option weight", "attractiveness": "Site attractiveness", "area_id": "Area reference", "site_id": "Location reference", "value": "Travel time in minutes", "distance_mode": "Distance method", "alpha": "Attractiveness exponent", "beta": "Distance decay", "distance_floor": "Minimum modeled distance", "access_threshold": "Access threshold", "demand_unit": "Demand unit", "period": "Time period", "attractiveness_definition": "Meaning of attractiveness"}
INTRO = "Use two sheets in one Excel file, or upload two CSV files together: customer areas and locations. Column names can be matched below."
QUICK = {
    "areas": {"title": "Customer areas", "aliases": ["areas", "zones", "customers", "demand"], "fields": {
        "name": ("Area name", "text", ["name", "area", "zone", "district"]),
        "latitude": ("Latitude", "optional_number", ["lat"]), "longitude": ("Longitude", "optional_number", ["lon", "lng", "long"]),
        "demand": ("Demand", "optional_number", ["population", "visits", "customers", "potential demand"]),
        "outside_weight": ("Outside-option weight", "optional_number", ["outside weight", "outside", "outside option"]),
        "note": ("Assumption or evidence note", "optional_text", ["note", "notes"]),
    }},
    "sites": {"title": "Locations", "aliases": ["sites", "stores", "branches", "outlets"], "fields": {
        "name": ("Location name", "text", ["name", "site", "location", "store", "branch"]),
        "role": ("Location type", "role", ["role", "type", "ownership"]),
        "latitude": ("Latitude", "optional_number", ["lat"]), "longitude": ("Longitude", "optional_number", ["lon", "lng", "long"]),
        "attractiveness": ("Site attractiveness", "optional_number", ["attractiveness", "attraction", "size"]),
        "note": ("Assumption or evidence note", "optional_text", ["note", "notes"]),
    }},
}
HELP = "Location type is Own, Competitor or Candidate. Use one demand unit and one positive attractiveness measure throughout. Outside-option weight represents unlisted alternatives or no visit; it is not a percentage. A blank stays unknown. This simple layout uses straight-line kilometres. Use the complete workbook for travel times."
EXAMPLES = {
    "areas": [{"name": "Example centre", "latitude": 59.915, "longitude": 10.750, "demand": 1200, "outside_weight": .15, "note": "Fictional area; demand and outside weight are assumptions"}, {"name": "Example north", "latitude": 59.975, "longitude": 10.750, "demand": 900, "outside_weight": .15, "note": "Fictional area; replace with your own data"}],
    "sites": [{"name": "Example existing café", "role": "Own", "latitude": 59.915, "longitude": 10.740, "attractiveness": 1, "note": "Fictional site and assumed attractiveness"}, {"name": "Example competitor", "role": "Competitor", "latitude": 59.930, "longitude": 10.820, "attractiveness": 1.1, "note": "Fictional site"}, {"name": "Example candidate", "role": "Candidate", "latitude": 59.966, "longitude": 10.752, "attractiveness": .9, "note": "Fictional site"}],
}


def build(brief, tables, settings, source):
    d = model.starter(brief)
    d["context"] = [{k: settings[k] for k in ("demand_unit", "period", "attractiveness_definition")}]
    d["parameters"] = [{"distance_mode": "straight_km", **{k: settings[k] for k in ("alpha", "beta", "distance_floor", "access_threshold")}}]
    d["sources"] = [{"id": "FILE1", "title": source[:300], "url": None, "note": "User-supplied geographic tables. Locations, demand and model assumptions require review."}]
    for table, prefix in [("areas", "Z"), ("sites", "L")]:
        rows = tables[table]
        if not rows:
            raise io.DataProblem("Include at least one customer area and one existing location.")
        names = [r["name"].casefold() for r in rows]
        if len(names) != len(set(names)):
            raise io.DataProblem(f"Repeated names in {TABLE_NAMES[table]}. Give each record a distinct name; duplicates are not combined.")
        d[table] = [{"id": f"{prefix}{i}", **r, "source_id": "FILE1"} for i, r in enumerate(rows, 1)]
    return model.validate(d)
