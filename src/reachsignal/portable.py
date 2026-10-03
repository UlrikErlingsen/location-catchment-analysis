"""Strict JSON, explicit local review and self-contained exports."""
from copy import deepcopy
from datetime import date
from html import escape
from io import BytesIO
import hashlib
import ipaddress
import json
import math
import re
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_DEFLATED

import pandas as pd
from jsonschema import Draft202012Validator, FormatChecker


class DataProblem(ValueError):
    pass


def obj(fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def text(size=1000, blank=False):
    return {"type": "string", "maxLength": size, **({} if blank else {"minLength": 1, "pattern": r"\S"})}


def number(low=0, high=1e12, nullable=False):
    spec = {"type": "number", "minimum": low, "maximum": high}
    return {"anyOf": [spec, {"type": "null"}]} if nullable else spec


def array(item, limit=500, minimum=0):
    return {"type": "array", "items": item, "minItems": minimum, "maxItems": limit}


ID = {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_-]{0,39}$"}
DATE = {"type": "string", "format": "date"}
SOURCE = obj({"id": ID, "title": text(300), "url": {"anyOf": [text(2000), {"type": "null"}]},
              "note": text(1500)})


def finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise DataProblem("Use finite numbers. Missing values must be null, not NaN or infinity.")
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    if isinstance(value, list):
        for item in value:
            finite(item)


def parse(payload):
    try:
        value = payload.decode("utf-8-sig") if isinstance(payload, bytes) else payload
        if len(value.encode("utf-8")) > 5_000_000:
            raise DataProblem("Keep the JSON file below 5 MB.")
        value = value.strip().lstrip("\ufeff")
        match = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n```", value, re.S | re.I)
        if match:
            value = match.group(1)
        def pairs(rows):
            result = {}
            for key, item in rows:
                if key in result:
                    raise DataProblem(f"Duplicate JSON key: {key}.")
                result[key] = item
            return result
        result = json.loads(value, object_pairs_hook=pairs)
        finite(result)
        if not isinstance(result, dict):
            raise DataProblem("Paste one JSON object.")
        return result
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise DataProblem("Invalid UTF-8 JSON. Paste only the complete object, without introductory prose.") from exc
    except ValueError as exc:
        if isinstance(exc, DataProblem):
            raise
        raise DataProblem("A JSON value is too large or invalid.") from exc


def safe_url(url):
    if any(c.isspace() or ord(c) < 32 for c in url) or "\\" in url:
        return False
    try:
        u = urlsplit(url)
        if u.scheme not in {"http", "https"} or not u.hostname or u.username or u.password:
            return False
        host = u.hostname.lower().rstrip(".")
        if "." not in host or host.endswith((".local", ".internal", ".localhost")):
            return False
        try:
            if not ipaddress.ip_address(host).is_global:
                return False
        except ValueError:
            pass
        return u.port is None or 1 <= u.port <= 65535
    except ValueError:
        return False


def validate_schema(data, schema):
    finite(data)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data))
    if errors:
        raise DataProblem("\n".join(f"{' / '.join(map(str, e.absolute_path)) or 'root'}: {e.message}" for e in errors[:6]))
    for source in data.get("sources", []):
        if source["url"] is not None and not safe_url(source["url"]):
            raise DataProblem(f"Source {source['id']}: use a public HTTP(S) link or null for supplied/internal material.")
    return deepcopy(data)


def unique(rows, field="id"):
    values = [r[field] for r in rows]
    if len(set(values)) != len(values):
        raise DataProblem(f"Duplicate {field} values are not allowed.")
    return {r[field]: r for r in rows}


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def project(app, data, origin="Imported AI draft"):
    return {"format": app + "-project-v1", "data": deepcopy(data), "origin": origin, "review": None}


def reviewed(p):
    return bool(p["review"] and p["review"]["data_sha256"] == digest(p["data"]))


def accept(p, name, note):
    if not name.strip() or not note.strip():
        raise DataProblem("Add your name and a note describing what you checked.")
    if len(name) > 120 or len(note) > 1500:
        raise DataProblem("The review name or note is too long.")
    p = deepcopy(p)
    p["review"] = {"reviewer": name.strip(), "note": note.strip(), "checked_on": date.today().isoformat(), "data_sha256": digest(p["data"])}
    return p


def restore(payload, app, validate):
    p = parse(payload)
    if set(p) != {"format", "data", "origin", "review"} or p["format"] != app + "-project-v1":
        raise DataProblem("This is not a saved project for this app. Use AI import for raw research JSON.")
    p["data"] = validate(p["data"])
    if not isinstance(p["origin"], str) or len(p["origin"]) > 200:
        raise DataProblem("Invalid project origin.")
    if p["review"] is not None:
        spec = obj({"reviewer": text(120), "note": text(1500), "checked_on": DATE,
                    "data_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}})
        validate_schema(p["review"], spec)
        if not reviewed(p):
            raise DataProblem("The saved review does not match the data. Import the data as a new draft and review it again.")
    return p


def json_bytes(data):
    return json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")


def csv_bytes(frame):
    def safe(value):
        if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
        return value
    return frame.apply(lambda col: col.map(safe)).to_csv(index=False).encode("utf-8-sig")


def report(title, p, sections, references, limits):
    e = lambda_string
    html = ["<!doctype html><html lang='en'><meta charset='utf-8'>", f"<title>{e(title)}</title>",
            "<style>body{font:15px/1.55 system-ui;color:#201e1d;max-width:1150px;margin:35px auto;padding:20px}"
            "h1,h2{color:#326384}table{border-collapse:collapse;width:100%;font-size:12px;overflow-wrap:anywhere}"
            "th,td{padding:8px;border:1px solid #ddd;text-align:left;vertical-align:top}th{background:#f5ead8}"
            ".blueprint{overflow:auto}.blueprint td{min-width:140px}.cell{margin:5px 0;padding:8px;border-radius:8px;background:#f9f4ed}"
            "@media print{body{margin:0;font-size:10pt}.blueprint{overflow:visible}.blueprint td{min-width:0}h2{break-after:avoid}thead{display:table-header-group}}"
            "</style><body>", f"<h1>{e(title)}</h1><p>{e(p['origin'])}</p>",
            f"<p>Scope: {e(p['data']['brief'])}</p><p>Review: {e(p['review'] or 'Unreviewed draft')}</p>"]
    if p["data"].get("context"):
        html.append("<h2>Units and scope</h2>" + pd.DataFrame(p["data"]["context"]).to_html(index=False, escape=True))
    for label, content in sections:
        html.append(f"<h2>{e(label)}</h2>")
        html.append(content.to_html(index=False, escape=True) if isinstance(content, pd.DataFrame) else content)
    html.append("<h2>Sources in this project</h2>")
    html.append(pd.DataFrame(p["data"].get("sources", [])).to_html(index=False, escape=True))
    html.append("<h2>Interpretation</h2><ul>" + "".join(f"<li>{e(x)}</li>" for x in limits) + "</ul><h2>Research</h2>")
    html.extend(f"<p><a href='{e(url)}'>{e(label)}</a></p>" for label, url in references)
    html.append(f"<p>Project SHA-256: {digest(p)}</p></body></html>")
    return "\n".join(html)


def lambda_string(value):
    return escape(str(value), quote=True)


def bundle(p, html, tables, references):
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as z:
        z.writestr("project.json", json_bytes(p))
        z.writestr("brief.html", html)
        z.writestr("references.json", json_bytes({"references": references, "project_sha256": digest(p)}))
        for label, table in tables.items():
            z.writestr(label + ".csv", csv_bytes(table))
    return buf.getvalue()
