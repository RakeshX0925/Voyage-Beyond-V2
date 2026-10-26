from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from flask import Flask, Response, abort, flash, make_response, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXOPLANET_FILE = DATA_DIR / "exoplanets.csv"
SOLAR_FILE = DATA_DIR / "solar_system.csv"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("VOYAGE_SECRET_KEY", "voyage-beyond-local-development-key")


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Normalize common null markers without fabricating measurement values.
    df = df.replace(r"^\s*$", np.nan, regex=True)
    df = df.replace(["--", "N/A", "n/a", "null", "None"], np.nan)
    return df


def exoplanets_raw() -> pd.DataFrame:
    return load_csv(EXOPLANET_FILE)


def exoplanets_clean() -> pd.DataFrame:
    return exoplanets_raw().drop_duplicates().reset_index(drop=True)


def solar_system() -> pd.DataFrame:
    return load_csv(SOLAR_FILE)


def safe_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = float(value)
        return parsed if np.isfinite(parsed) else None
    except ValueError:
        return None


def apply_planet_filters(df: pd.DataFrame, args: Any) -> pd.DataFrame:
    """Apply only filters supported by the columns present in the supplied CSV."""
    result = df.copy()
    q = (args.get("q", "") or "").strip().casefold()
    if q:
        searchable = []
        for col in ("pl_name", "hostname"):
            if col in result.columns:
                searchable.append(result[col].fillna("").astype(str).str.casefold().str.contains(q, regex=False))
        if searchable:
            mask = searchable[0]
            for part in searchable[1:]:
                mask = mask | part
            result = result[mask]

    method = (args.get("method", "") or "").strip()
    if method and "discoverymethod" in result.columns:
        result = result[result["discoverymethod"].fillna("").astype(str) == method]

    year = safe_float(args.get("year"))
    if year is not None and "disc_year" in result.columns:
        result = result[pd.to_numeric(result["disc_year"], errors="coerce") >= year]

    for param, col, op in [
        ("min_mass", "pl_bmasse", "min"), ("max_mass", "pl_bmasse", "max"),
        ("min_radius", "pl_rade", "min"), ("max_radius", "pl_rade", "max")
    ]:
        value = safe_float(args.get(param))
        if value is not None and col in result.columns:
            numeric = pd.to_numeric(result[col], errors="coerce")
            result = result[numeric >= value] if op == "min" else result[numeric <= value]
    return result


def frame_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    # Convert NaN/NumPy values into template-safe Python values.
    clean = df.astype(object).where(pd.notna(df), None)
    return clean.to_dict(orient="records")


@app.template_filter("number_format")
def number_format(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"


@app.template_filter("display_num")
def display_num(value: Any) -> str:
    if value is None or pd.isna(value):
        return "—"
    try:
        number = float(value)
        if not np.isfinite(number):
            return "—"
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.4f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        message = (request.form.get("message") or "").strip()
        if not name or not email or not message:
            flash("Please complete all fields.", "error")
        else:
            # This project intentionally does not persist or email submitted personal data.
            flash("Thanks for your feedback! This demo has validated your message.", "success")
            return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/dashboard")
def dashboard():
    df = exoplanets_raw()
    solar = solar_system()
    if df.empty:
        abort(500, "The exoplanet dataset could not be loaded.")
    years = pd.to_numeric(df["disc_year"], errors="coerce").dropna().astype(int)
    year_counts = years.value_counts().sort_index()
    methods = df["discoverymethod"].fillna("Unknown").astype(str).value_counts().head(8)
    orbital = pd.to_numeric(df["pl_orbper"], errors="coerce")
    stats = {
        "total_exoplanets": len(df),
        "host_stars": df["hostname"].nunique(dropna=True),
        "discovery_methods": df["discoverymethod"].nunique(dropna=True),
        "solar_objects": len(solar),
        "missing_names": int(df["pl_name"].isna().sum()),
        "missing_periods": int(orbital.isna().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "avg_orbital_period": f"{orbital.mean():,.2f}" if orbital.notna().any() else "N/A",
    }
    charts = {
        "years": year_counts.index.tolist(),
        "year_counts": year_counts.tolist(),
        "methods": methods.index.tolist(),
        "method_counts": methods.tolist(),
    }
    return render_template("dashboard.html", stats=stats, charts=charts)


@app.route("/explorer")
@app.route("/explore")
def explorer():
    df = exoplanets_raw()
    required = {"pl_name", "hostname", "discoverymethod", "disc_year", "pl_orbper", "pl_rade", "pl_bmasse", "sy_dist"}
    if df.empty:
        abort(500, "The exoplanet dataset is empty or could not be loaded. Check that data/exoplanets.csv exists.")
    missing = required.difference(df.columns)
    if missing:
        abort(500, "The exoplanet dataset is missing expected columns: " + ", ".join(sorted(missing)))

    filtered = apply_planet_filters(df, request.args)
    raw_page = (request.args.get("page", "1") or "1").strip()
    try:
        page = max(1, int(raw_page))
    except (TypeError, ValueError):
        page = 1
    page_size = 100
    pages = max(1, int(np.ceil(len(filtered) / page_size)))
    page = min(page, pages)
    start = (page - 1) * page_size
    methods = sorted(df["discoverymethod"].dropna().astype(str).unique().tolist())
    filter_keys = ["q", "method", "year", "min_mass", "max_mass", "min_radius", "max_radius"]
    filters = {key: request.args.get(key, "") for key in filter_keys}
    return render_template(
        "explorer.html", rows=frame_records(filtered.iloc[start:start + page_size]),
        total=len(df), shown=len(filtered), page=page, pages=pages, methods=methods,
        filters=filters
    )


@app.route("/download/exoplanets.csv")
def download_exoplanets():
    df = apply_planet_filters(exoplanets_raw(), request.args)
    return csv_response(df, "voyage_beyond_filtered_exoplanets.csv")


@app.route("/compare")
def compare():
    df = exoplanets_raw()
    names = df["pl_name"].dropna().astype(str).drop_duplicates().sort_values().tolist()
    selected = request.args.getlist("planet")
    # Limit selection to keep charts and tables readable.
    selected = [name for name in selected if name in set(names)][:8]
    rows = df[df["pl_name"].astype(str).isin(selected)].drop_duplicates("pl_name")
    return render_template("compare.html", planet_options=names, selected=selected, selected_rows=frame_records(rows))


@app.route("/cleaning")
def cleaning():
    raw = exoplanets_raw()
    normalized = raw.replace(r"^\s*$", np.nan, regex=True)
    cleaned = normalized.drop_duplicates().reset_index(drop=True)
    total_cells = int(normalized.shape[0] * normalized.shape[1])
    missing_cells = int(normalized.isna().sum().sum())
    report = {
        "raw_rows": len(raw),
        "duplicate_rows": int(normalized.duplicated().sum()),
        "rows_after_dedup": len(cleaned),
        "missing_cells": missing_cells,
        "columns": [{
            "name": col,
            "dtype": str(normalized[col].dtype),
            "missing": int(normalized[col].isna().sum()),
            "missing_pct": round(float(normalized[col].isna().mean() * 100), 2) if len(normalized) else 0,
            "unique": int(normalized[col].nunique(dropna=True)),
        } for col in normalized.columns],
        "total_cells": total_cells,
    }
    return render_template("cleaning.html", report=report)


@app.route("/download/cleaned.csv")
def download_cleaned():
    return csv_response(exoplanets_clean(), "voyage_beyond_cleaned_exoplanets.csv")


@app.route("/analytics")
def analytics():
    df = exoplanets_raw()
    year_series = pd.to_numeric(df["disc_year"], errors="coerce").dropna().astype(int)
    years = year_series.value_counts().sort_index()
    radius = pd.to_numeric(df["pl_rade"], errors="coerce").dropna()
    valid = df.copy()
    for col in ["pl_rade", "pl_bmasse", "disc_year"]:
        valid[col] = pd.to_numeric(valid[col], errors="coerce")
    valid = valid.dropna(subset=["pl_rade", "pl_bmasse"])
    # Keep plots usable and resistant to extreme outliers in the supplied catalogue.
    valid = valid[(valid["pl_rade"] > 0) & (valid["pl_bmasse"] > 0)].head(2500)
    charts = {
        "trend": {"x": years.index.tolist(), "y": years.tolist()},
        "radius": radius[(radius > 0) & (radius <= radius.quantile(.99))].tolist(),
        "scatter": {
            "radius": valid["pl_rade"].tolist(),
            "mass": valid["pl_bmasse"].tolist(),
            "year": valid["disc_year"].fillna(0).astype(int).tolist(),
            "names": valid["pl_name"].fillna("Unknown").astype(str).tolist(),
        }
    }
    return render_template("analytics.html", charts=charts)


@app.route("/habitability")
def habitability():
    df = exoplanets_raw()
    minr = safe_float(request.args.get("minr"))
    maxr = safe_float(request.args.get("maxr"))
    maxp = safe_float(request.args.get("maxp"))
    maxdist = safe_float(request.args.get("maxdist"))
    # Defaults on first load, but explicit zero values remain valid.
    minr = 0.5 if minr is None else minr
    maxr = 1.8 if maxr is None else maxr
    maxp = 365.25 if maxp is None else maxp
    result = df.copy()
    radius = pd.to_numeric(result["pl_rade"], errors="coerce")
    period = pd.to_numeric(result["pl_orbper"], errors="coerce")
    result = result[radius.between(minr, maxr) & period.le(maxp)]
    if maxdist is not None:
        distance = pd.to_numeric(result["sy_dist"], errors="coerce")
        result = result[distance.le(maxdist)]
    filters = {"minr": request.args.get("minr", "0.5"), "maxr": request.args.get("maxr", "1.8"),
               "maxp": request.args.get("maxp", "365.25"), "maxdist": request.args.get("maxdist", "")}
    return render_template("habitability.html", rows=frame_records(result.head(100)), count=len(result), filters=filters)


@app.route("/download/habitability.csv")
def download_habitability():
    args = request.args
    df = exoplanets_raw()
    minr = safe_float(args.get("minr")); maxr = safe_float(args.get("maxr")); maxp = safe_float(args.get("maxp"))
    minr = 0.5 if minr is None else minr
    maxr = 1.8 if maxr is None else maxr
    maxp = 365.25 if maxp is None else maxp
    radius = pd.to_numeric(df["pl_rade"], errors="coerce")
    period = pd.to_numeric(df["pl_orbper"], errors="coerce")
    result = df[radius.between(minr, maxr) & period.le(maxp)].copy()
    maxdist = safe_float(args.get("maxdist"))
    if maxdist is not None:
        distance = pd.to_numeric(result["sy_dist"], errors="coerce")
        result = result[distance.le(maxdist)]
    return csv_response(result, "voyage_beyond_habitability_candidates.csv")


@app.route("/solar-system", endpoint="solar_system")
def solar_system_page():
    df = solar_system()
    radius = pd.to_numeric(df.get("mean_radius_km", pd.Series(dtype=float)), errors="coerce")
    density = pd.to_numeric(df.get("bulk_density_g_cm3", pd.Series(dtype=float)), errors="coerce")
    escape = pd.to_numeric(df.get("escape_velocity_km_s", pd.Series(dtype=float)), errors="coerce")
    return render_template("solar_system.html", objects=frame_records(df),
        avg_radius=f"{radius.mean():,.1f}" if radius.notna().any() else "N/A",
        avg_density=f"{density.mean():,.2f}" if density.notna().any() else "N/A",
        avg_escape=f"{escape.mean():,.2f}" if escape.notna().any() else "N/A")


@app.route("/download/solar-system.csv")
def download_solar():
    return csv_response(solar_system(), "voyage_beyond_solar_system.csv")


def csv_response(df: pd.DataFrame, filename: str) -> Response:
    response = make_response(df.to_csv(index=False))
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@app.errorhandler(500)
def internal_error(error):
    return render_template("error.html", code=500, message=getattr(error, "description", "An unexpected error occurred.")), 500


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="That destination could not be found."), 404


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
