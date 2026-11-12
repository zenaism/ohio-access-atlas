"""Assistant tools on the real knowledge base built from the committed map data."""

import pytest

from atlas.assistant import tools


@pytest.fixture(scope="module", autouse=True)
def _kb():
    tools.connect(rebuild=True).close()


def test_search_prefers_rare_name_words():
    assert tools.search_places("Smale Riverfront Park", limit=1)[0]["name"] == "Smale Riverfront Park"


def test_search_region_filter_keeps_unknowns_unknown():
    # the only Skyline in the data is in Oxford: a Cincinnati search must not return it
    assert tools.search_places("Skyline Ludlow", region="cincinnati") == []


def test_need_filter_and_organizations():
    names = [p["name"] for p in tools.search_places(need="all_terrain_chair")]
    assert "MetroParks of Butler County" in names  # an organization record, no map point


def test_nearest_is_sorted_and_has_direction():
    res = tools.nearest(39.1016, -84.5126, need="accessible_restroom", max_miles=1)
    assert res and [r["miles"] for r in res] == sorted(r["miles"] for r in res)
    assert all(r["direction"] in tools.COMPASS for r in res)


def test_get_place_carries_evidence():
    p = tools.get_place("Aronoff Center for the Arts")
    assert p["facts"] and all(f["source"].startswith("http") for f in p["facts"])
    assert any(f["quote"] for f in p["facts"])


def test_events_by_access_kind():
    ev = tools.find_events(
        region="cincinnati", access=["audio_description"], start="2026-11-01", end="2027-06-30"
    )
    assert ev and all("audio_description" in e["access"] for e in ev)
    assert [e["start"] for e in ev] == sorted(e["start"] for e in ev)


def test_query_may_be_a_number():
    assert isinstance(tools.search_places(311), list)
