"""Rules that decide what the map says about a place: rating, the 'What is known' line, summaries,
directions in words, and page dates. These are the sentences a blind user hears, so they are pinned."""

import os
import time

import pandas as pd
import pytest
from shapely.geometry import Point

from atlas import core
from atlas.connectors import web
from atlas.export_map import _feet, _phrase, _stop, _towards, key_facts, rate, summarise
from atlas.place_pages import _access, _when


def facts(*rows):
    return pd.DataFrame(rows, columns=["attribute", "value"])


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ([], "unknown"),
        ([("entrance_step_free", "yes"), ("restroom_accessible", "yes")], "accessible"),
        ([("entrance_step_free", "yes")], "partial"),
        ([("entrance_step_free", "no"), ("restroom_accessible", "yes")], "not_accessible"),
        ([("notice", "yes")], "unknown"),  # a warning is not evidence of access
        ([("notice", "yes"), ("elevator", "yes")], "partial"),
    ],
)
def test_rate(rows, expected):
    assert rate(facts(*rows)) == expected


def place(layer="culture", *fs):
    return {"layer": layer, "facts": [{"attribute": a, "value": v, "detail": d} for a, v, d in fs]}


def test_key_facts_always_name_entrance_and_restroom():
    keys = key_facts(place("culture", ("Elevator / lift", "yes", ""), ("Braille", "yes", "")))
    assert keys[:2] == [["Entrance", "not known"], ["Restroom", "not known"]]
    assert ["Elevator", "yes"] in keys and ["Braille", "yes"] in keys


def test_key_facts_yes_beats_no_and_limited_reads_partly():
    keys = dict(
        key_facts(
            place(
                "culture",
                ("Step-free entrance", "no", ""),
                ("Accessible entrance", "yes", ""),
                ("Accessible parking", "limited", ""),
            )
        )
    )
    assert keys["Entrance"] == "yes" and keys["Parking"] == "partly"


def test_key_facts_empty_for_restrooms_and_unknowns():
    assert key_facts(place("restroom", ("wheelchair", "yes", ""))) == []
    assert key_facts(place("culture")) == []


def test_summary_says_notice_first_and_once():
    s = summarise(place("park", ("Notice", "yes", "trail closed until spring")))
    assert s.startswith("Notice: trail closed until spring.")
    assert s.count("trail closed") == 1


def test_phrase():
    assert _phrase("trail_surface", "yes", "paved") == "accessible path (paved)"
    assert _phrase("elevator", "no", "") == "no elevator / lift"
    assert _phrase("ramp_steep", "no", "") is None
    assert _phrase("elevator", "yes", "x" * 101) == "elevator / lift"  # long details stay in Details


@pytest.mark.parametrize(("dx", "dy", "word"), [(0, 10, "north"), (10, 0, "east"), (-10, -10, "southwest")])
def test_towards(dx, dy, word):
    assert _towards(Point(0, 0), Point(dx, dy)) == word


def test_feet_and_stop_names():
    assert _feet(3) == "about 50 feet" and _feet(61) == "about 200 feet"
    assert _stop("CENTRAL PKWY & 6TH ST") == "Central Pkwy & 6th St"
    assert _stop("King Library") == "King Library"


def test_page_dates_and_access_words():
    assert _when("2026-12-05T14:00") == "Saturday, December 5, 2026, 2 PM"
    assert _when("2027-03-16T19:30") == "Tuesday, March 16, 2027, 7:30 PM"
    assert (
        _access({"access": ["audio_description", "asl"]})
        == " <strong>(audio described, ASL interpreted)</strong>"
    )
    assert _access({"accessible_tag": True}) == " (listed as accessible)"


def test_refresh_age(monkeypatch, tmp_path):
    rec = {"retrieved_at": "2020-01-01T00:00:00+00:00"}
    monkeypatch.delenv("ATLAS_MAX_AGE_DAYS", raising=False)
    assert not web._too_old(rec)  # normal runs never re-fetch
    monkeypatch.setenv("ATLAS_MAX_AGE_DAYS", "6")
    assert web._too_old(rec)
    f = tmp_path / "x.bin"
    f.write_bytes(b"x")
    assert not core._expired(f)
    old = time.time() - 7 * 86400
    os.utime(f, (old, old))
    assert core._expired(f)
