import json

from atlas.google_places import browser_api_key, matched_place_ids, place_match_rows
from atlas.map_viewer import render


def test_browser_key_uses_explicit_browser_setting(monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_BROWSER_API_KEY", "restricted-browser-key")

    assert browser_api_key() == "restricted-browser-key"


def test_only_matched_place_ids_are_passed_to_the_map():
    records = {
        "matched": {
            "matched": True,
            "google_id": "places/one",
            "accessibility": {"wheelchairAccessibleEntrance": True},
        },
        "unmatched": {"matched": False, "google_id": "places/two"},
        "missing": {"matched": True, "accessibility": {"wheelchairAccessibleEntrance": False}},
    }

    assert matched_place_ids(records) == {"matched": "places/one"}


def test_place_match_rows_join_atlas_features_with_matched_place_ids():
    feature = {
        "type": "Feature",
        "id": "cincinnati:0",
        "geometry": {"type": "Point", "coordinates": [-84.5, 39.1]},
        "properties": {
            "link_id": "matched",
            "name": "Example venue",
            "layer": "culture",
            "access_rating": "partial",
        },
    }

    rows = place_match_rows(
        {"cincinnati": {"features": [feature]}},
        {"matched": "places/one", "unmatched": "places/two"},
    )

    assert len(rows) == 1
    assert rows[0]["google_place_id"] == "places/one"
    assert rows[0]["name"] == "Example venue"
    assert json.loads(rows[0]["atlas_feature_json"]) == feature


def test_existing_map_keeps_original_basemap_and_uses_google_places_when_key_is_configured():
    data = {
        "cincinnati": {
            "features": [{"properties": {"link_id": "matched"}}]
        }
    }

    html = render(
        data,
        google_api_key="restricted-browser-key",
        google_place_ids={"matched": "places/one", "not-in-this-map": "places/two"},
    )

    assert "maps.googleapis.com/maps/api/js?key=restricted-browser-key" in html
    assert "basemap.nationalmap.gov" in html
    assert "const GOOGLE_ENABLED = false" in html
    assert "google.maps.importLibrary('places')" in html
    assert "google.maps.importLibrary('maps')" not in html
    assert '"matched": "places/one"' in html
    assert "places/two" not in html
    assert "place.fetchFields" in html
    assert "hasWheelchairAccessibleEntrance" in html
    assert '"accessibilityOptions":' not in html


def test_existing_map_keeps_its_original_basemap_without_browser_key():
    html = render({"cincinnati": {"features": []}}, google_place_ids={"matched": "places/one"})

    assert "basemap.nationalmap.gov" in html
    assert "maps.googleapis.com/maps/api/js" not in html
    assert "places/one" not in html
