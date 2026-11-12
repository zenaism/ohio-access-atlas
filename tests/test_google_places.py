from atlas.google_places import browser_api_key, matched_place_ids
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


def test_existing_map_uses_google_basemap_and_matched_ids_when_key_is_configured():
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
