"""Turn work/places.geojson into Google-Maps-ready files, grouped by category.

  python -m pipeline.export_maps                 # KML + KMZ + CSV into work/maps/
  python -m pipeline.export_maps --format kml    # one format (kml | kmz | csv | all)
  python -m pipeline.export_maps --regeocode     # fill in any missing pins first, then export
  python -m pipeline.export_maps --out DIR       # write somewhere else

KML and KMZ import into Google My Maps and Google Earth and keep the category grouping; CSV
imports into Google My Maps (Latitude/Longitude columns) and opens in Sheets or Excel. The
consumer Google Maps app cannot open these files directly: create the map once in My Maps
(mymaps.google.com), and it then shows in the Maps app under Saved, Maps on every device
signed into the same account.
"""
from __future__ import annotations

import argparse
import csv
import html
import io
import json
import urllib.parse
import zipfile
from collections import defaultdict
from pathlib import Path

from . import config, places

# Google "ms" dot icons that exist, cycled across categories so each list reads at a glance.
_COLORS = ["red", "blue", "green", "orange", "purple", "yellow", "ltblue", "pink"]


def _features(workdir) -> list:
    path = workdir / "places.geojson"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("features", [])
    except Exception:
        return []


def _is_mapped(f) -> bool:
    g = f.get("geometry")
    if not g or g.get("type") != "Point":
        return False
    c = g.get("coordinates")
    if not (isinstance(c, list) and len(c) >= 2):
        return False
    return (f.get("properties") or {}).get("loc_flag") != "country_mismatch_review"


def _maps_link(lat, lng) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"


def to_csv(features) -> str:
    """A My Maps / Sheets row per mapped place (Latitude and Longitude are the position columns)."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Name", "Latitude", "Longitude", "Category", "Region", "City", "Country",
                "Price", "Why", "Creator", "SourceURL", "GoogleMapsLink"])
    for f in features:
        p = f.get("properties", {})
        lng, lat = f["geometry"]["coordinates"][:2]
        w.writerow([p.get("name", ""), lat, lng, p.get("category", ""), p.get("region", ""),
                    p.get("city", ""), p.get("country", ""), p.get("price", ""), p.get("why", ""),
                    p.get("creator", ""), p.get("source_url", ""), _maps_link(lat, lng)])
    return buf.getvalue()


def to_kml(features) -> str:
    """One <Folder> per category (an organized list in My Maps / Earth), with a styled pin each."""
    by_cat = defaultdict(list)
    for f in features:
        by_cat[(f.get("properties", {}).get("category") or "other").strip() or "other"].append(f)
    cats = sorted(by_cat, key=lambda c: (-len(by_cat[c]), c))
    style = {c: _COLORS[i % len(_COLORS)] for i, c in enumerate(cats)}
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>Grand Log places</name>']
    for c in cats:
        out.append(f'<Style id="cat-{html.escape(c)}"><IconStyle><Icon>'
                   f'<href>http://maps.google.com/mapfiles/ms/icons/{style[c]}-dot.png</href>'
                   f'</Icon></IconStyle></Style>')
    for c in cats:
        out.append(f"<Folder><name>{html.escape(c)} ({len(by_cat[c])})</name>")
        for f in by_cat[c]:
            p = f.get("properties", {})
            lng, lat = f["geometry"]["coordinates"][:2]
            out.append("<Placemark>"
                       f"<name>{html.escape(p.get('name') or 'Saved place')}</name>"
                       f"<description>{_desc(p, lat, lng)}</description>"
                       f"<styleUrl>#cat-{html.escape(c)}</styleUrl>"
                       f"<Point><coordinates>{lng},{lat},0</coordinates></Point></Placemark>")
        out.append("</Folder>")
    out.append("</Document></kml>")
    return "\n".join(out)


def _desc(p, lat, lng) -> str:
    rows = []
    where = ", ".join(x for x in (p.get("city"), p.get("region"), p.get("country")) if x)
    if where:
        rows.append(f"<b>Where:</b> {html.escape(where)}")
    if p.get("price"):
        rows.append(f"<b>Price:</b> {html.escape(p['price'])}")
    if p.get("why"):
        rows.append(f"<b>Why:</b> {html.escape(p['why'])}")
    if p.get("creator"):
        rows.append(f"<b>Saved from:</b> @{html.escape(p['creator'])}")
    if p.get("source_url"):
        rows.append(f'<a href="{html.escape(p["source_url"])}">Original post</a>')
    rows.append(f'<a href="{html.escape(_maps_link(lat, lng))}">Open in Google Maps</a>')
    return "<![CDATA[" + "<br>".join(rows) + "]]>"


def _unmapped_csv(features) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Name", "Category", "City", "Country", "GoogleMapsSearch"])
    for f in features:
        p = f.get("properties", {})
        q = " ".join(x for x in (p.get("name"), p.get("city"), p.get("country")) if x)
        link = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(q)}" if q else ""
        w.writerow([p.get("name", ""), p.get("category", ""), p.get("city", ""),
                    p.get("country", ""), link])
    return buf.getvalue()


def export(workdir=None, formats=("kml", "kmz", "csv"), out=None) -> dict:
    """Write the requested formats plus unmapped.csv. Returns {format: path, ..., count: N}."""
    workdir = workdir or config.WORKDIR
    out = out or (workdir / "maps")
    out.mkdir(parents=True, exist_ok=True)
    feats = _features(workdir)
    mapped = [f for f in feats if _is_mapped(f)]
    unmapped = [f for f in feats if not _is_mapped(f)]
    fmts = {"kml", "kmz", "csv"} if "all" in set(formats) else set(formats)
    written = {}
    if fmts & {"kml", "kmz"}:
        kml = to_kml(mapped)
        if "kml" in fmts:
            (out / "places.kml").write_text(kml, encoding="utf-8")
            written["kml"] = str(out / "places.kml")
        if "kmz" in fmts:
            with zipfile.ZipFile(out / "places.kmz", "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("doc.kml", kml)
            written["kmz"] = str(out / "places.kmz")
    if "csv" in fmts:
        (out / "places.csv").write_text(to_csv(mapped), encoding="utf-8", newline="")
        written["csv"] = str(out / "places.csv")
    (out / "unmapped.csv").write_text(_unmapped_csv(unmapped), encoding="utf-8", newline="")
    written["unmapped"] = str(out / "unmapped.csv")
    written["count"] = len(mapped)
    return written


def refresh() -> None:
    """Best-effort regenerate every export file. Never raises (called after a place capture)."""
    try:
        export()
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Export work/places.geojson for Google Maps.")
    ap.add_argument("--format", choices=["kml", "kmz", "csv", "all"], default="all")
    ap.add_argument("--out", help="output directory (default: work/maps)")
    ap.add_argument("--regeocode", action="store_true",
                    help="geocode any places still missing coordinates, then export")
    args = ap.parse_args()
    if args.regeocode:
        recovered, remaining = places.regeocode_missing()
        print(f"re-geocoded {recovered} place(s); {remaining} still without coordinates")
    out = Path(args.out).resolve() if args.out else None
    written = export(formats=(args.format,), out=out)
    print(f"exported {written.pop('count')} mapped places:")
    for fmt, path in written.items():
        print(f"  {fmt}: {path}")


if __name__ == "__main__":
    main()
