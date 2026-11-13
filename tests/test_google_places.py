import json

from atlas.google_places import (
    enrich_google_places,
    legacy_google_place,
    matched_place_ids,
    place_match_rows,
)
from atlas.map_viewer import render


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


def test_legacy_google_accessibility_cache_is_normalized_to_place_details():
    detail = legacy_google_place(
        {
            "matched": True,
            "google_id": "places/one",
            "google_name": "Example venue",
            "url": "https://maps.google.com/?cid=1",
            "distance_m": 42.5,
            "accessibility": {
                "wheelchairAccessibleEntrance": True,
                "wheelchairAccessibleRestroom": False,
            },
        }
    )

    assert detail == {
        "id": "places/one",
        "displayName": {"text": "Example venue"},
        "googleMapsUri": "https://maps.google.com/?cid=1",
        "accessibilityOptions": {
            "hasWheelchairAccessibleEntrance": True,
            "hasWheelchairAccessibleRestroom": False,
        },
        "legacyMatchDistanceMeters": 42.5,
    }


def test_google_details_are_attached_only_to_features_with_matching_place_ids():
    data = {
        "cincinnati": {
            "features": [
                {"properties": {"link_id": "matched"}},
                {"properties": {"link_id": "mismatch"}},
                {"properties": {"link_id": "unmatched"}},
            ]
        }
    }

    enrich_google_places(
        data,
        {"matched": "places/one", "mismatch": "places/two"},
        {
            "matched": {"id": "places/one", "displayName": {"text": "Example"}},
            "mismatch": {"id": "places/other"},
        },
    )

    assert data["cincinnati"]["features"][0]["properties"]["google_place_id"] == "places/one"
    assert data["cincinnati"]["features"][0]["properties"]["google_place"]["id"] == "places/one"
    assert "google_place" not in data["cincinnati"]["features"][1]["properties"]
    assert "google_place_id" not in data["cincinnati"]["features"][2]["properties"]


def test_existing_map_uses_saved_google_details_without_live_api_or_key():
    data = {
        "cincinnati": {
            "features": [
                {
                    "properties": {
                        "link_id": "matched",
                        "google_place": {
                            "id": "places/one",
                            "displayName": {"text": "Example venue"},
                            "googleMapsUri": "https://maps.google.com/?cid=1",
                            "accessibilityOptions": {"hasWheelchairAccessibleEntrance": True},
                        },
                    }
                }
            ]
        }
    }

    html = render(data)

    assert "basemap.nationalmap.gov" in html
    assert "maps.googleapis.com/maps/api/js" not in html
    assert "place.fetchFields" not in html
    assert "Loading live accessibility details" not in html
    assert "Example venue" in html
    assert "googleMapsUri" in html
    assert "hasWheelchairAccessibleEntrance" in html


def test_existing_map_keeps_its_original_basemap_without_browser_key():
    html = render({"cincinnati": {"features": []}})

    assert "basemap.nationalmap.gov" in html
    assert "maps.googleapis.com/maps/api/js" not in html


def test_ratings_config_needs_https_url_and_key(tmp_path):
    from atlas.map_viewer import ratings_config

    cfg = tmp_path / "ratings.yaml"
    assert ratings_config(tmp_path / "missing.yaml") is None
    cfg.write_text('url: ""\nkey: ""\n')
    assert ratings_config(cfg) is None
    cfg.write_text('url: "http://x.supabase.co"\nkey: "k"\n')
    assert ratings_config(cfg) is None
    cfg.write_text('url: "https://x.supabase.co/"\nkey: "sb_publishable_k"\n')
    assert ratings_config(cfg) == {"url": "https://x.supabase.co", "key": "sb_publishable_k"}
