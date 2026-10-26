import io
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import app as voyage


def client():
    voyage.app.config.update(TESTING=True)
    return voyage.app.test_client()


def test_main_pages_load():
    c = client()
    for path in ["/", "/about", "/gallery", "/quiz", "/contact", "/dashboard",
                 "/explorer", "/compare", "/cleaning", "/analytics",
                 "/habitability", "/solar-system"]:
        response = c.get(path)
        assert response.status_code == 200, path


def test_explorer_filters_and_csv_download():
    c = client()
    response = c.get("/explorer?q=55%20Cnc")
    assert response.status_code == 200
    assert b"55 Cnc" in response.data
    csv = c.get("/download/exoplanets.csv?q=55%20Cnc")
    assert csv.status_code == 200
    assert "text/csv" in csv.headers["Content-Type"]
    assert b"pl_name" in csv.data


def test_cleaning_download_is_csv():
    response = client().get("/download/cleaned.csv")
    assert response.status_code == 200
    assert b"pl_name" in response.data


def test_contact_validation_and_acknowledgement():
    c = client()
    response = c.post("/contact", data={"name": "Test", "email": "test@example.com", "message": "Hello"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"validated your message" in response.data


def test_habitability_and_solar_downloads():
    c = client()
    assert c.get("/habitability?minr=0.5&maxr=2&maxp=500").status_code == 200
    assert c.get("/download/solar-system.csv").status_code == 200


def test_explore_alias_and_invalid_page_load():
    c = client()
    assert c.get("/explore").status_code == 200
    assert c.get("/explorer?page=not-a-number").status_code == 200


def test_explorer_pagination_preserves_filters():
    c = client()
    response = c.get("/explorer?method=Transit")
    assert response.status_code == 200
    assert b"method=Transit" in response.data
    assert b"page=2" in response.data


def test_about_describes_python_data_lab():
    response = client().get("/about")
    assert response.status_code == 200
    assert b"Python" in response.data
    assert b"Data Cleaning Lab" in response.data
