# Voyage Beyond — Space Learning & Data Exploration

Voyage Beyond preserves the original space-themed learning site and extends it into a Python-powered astronomy data project. The original Home, About, Gallery, Quiz, and Contact pages remain available alongside the data lab. The shared UI uses a responsive cosmic glassmorphism style across pages.

## Features

- **Home and About:** project overview, learning paths, tools, dataset details, and technology stack.
- **Space Data Dashboard:** dataset counts, host-star and discovery-method summaries, data-quality indicators, and interactive charts.
- **Planet Explorer:** search by planet/host name and filter by discovery method, year, mass, and radius.
- **CSV export:** download filtered exoplanet records.
- **Planet Comparison:** compare available measurements for up to eight selected exoplanets.
- **Data Cleaning Lab:** inspect missing values and exact duplicates, and export a de-duplicated dataset.
- **Interactive Analytics:** discovery-year trend, planet-radius distribution, and mass-versus-radius plot.
- **Habitability Candidate Explorer:** filter by radius, orbital period, and optional system distance. This is a shortlist tool, not a life detector.
- **Solar System Explorer:** inspect physical parameters and download the supplied Solar System CSV.
- **Gallery and Quiz:** image lightbox and five-question space quiz.
- **Contact demo:** validates the form and acknowledges feedback; it does not email or save personal details.

## Datasets

- `data/exoplanets.csv` — 6,451 rows and 8 columns in the supplied copy: `pl_name`, `hostname`, `discoverymethod`, `disc_year`, `pl_orbper`, `pl_rade`, `pl_bmasse`, and `sy_dist`.
- `data/solar_system.csv` — 13 rows of Solar System object measurements, including radius, mass, density, rotation/orbital periods, gravity, and escape velocity where available.

The application calculates summaries from the local CSV files. Missing measurements remain missing; the project does not replace them with zero or invent scientific values. The exoplanet file does not contain enough environmental information to determine whether a planet is habitable.

## Requirements

- Python 3.10 or newer
- Dependencies listed in `requirements.txt` (production) and `requirements-dev.txt` (includes pytest)
- Internet access is needed for the externally hosted Plotly chart library, Google font, and remote background/gallery imagery. Core Flask routes and local CSV processing run locally.

## Run on Windows

1. Install Python 3.10 or newer.
2. Open this project folder in VS Code.
3. Open a terminal in the project folder and run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python app.py
   ```

4. Visit `http://127.0.0.1:5000`.

Alternatively, run `run_windows.bat` after dependencies are installed.

## Run on macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python app.py
```

## Tests

```bash
python -m pytest -q
```

The test suite checks page routes, Explorer filtering and pagination fallback, CSV downloads, contact-form acknowledgement, and candidate/solar-data routes.

## Page map

| URL | Purpose |
|---|---|
| `/` | Home |
| `/about` | Project overview and technologies |
| `/gallery` | Cosmic gallery |
| `/quiz` | Space quiz |
| `/contact` | Feedback demo |
| `/dashboard` | Dataset summary dashboard |
| `/explorer` or `/explore` | Search/filter exoplanets |
| `/compare` | Planet comparison |
| `/analytics` | Interactive charts |
| `/cleaning` | Data-quality report and cleaned export |
| `/habitability` | Candidate filters |
| `/solar-system` | Solar System physical data |

## Deployment note

For deployment, set a strong `VOYAGE_SECRET_KEY` environment variable and keep Flask debug mode disabled. The default secret is intended only for local development.

## Deploy on Render

This repository includes `render.yaml` for a straightforward Render deployment.

1. Push the project folder contents to a GitHub repository (the folder containing `app.py`, `requirements.txt`, `templates/`, `static/`, and `data/` should be the repository root).
2. In Render, choose **New → Blueprint** and connect the GitHub repository, or choose **New → Web Service**.
3. If using a Blueprint, Render reads `render.yaml`. If creating a Web Service manually, set the build command to `pip install -r requirements.txt` and the start command to `gunicorn app:app`.
4. Ensure `VOYAGE_SECRET_KEY` is set to a strong random secret and `FLASK_DEBUG` is `0`. The included Blueprint generates a secret automatically. Never commit real `.env` files or secret values.
5. Deploy and inspect the service logs. Test the home page and data pages on the live URL.

The app reads its CSV datasets from `data/`, so keep both CSV files in the repository. Render free web services may sleep after inactivity and take a little time to wake up.

## Development tests

Install development dependencies with `python -m pip install -r requirements-dev.txt`, then run `python -m pytest -q`. Keep `tests/` in GitHub; it is useful project source and is not served as a public website page.
