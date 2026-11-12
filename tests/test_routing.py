"""Wheelchair routing on the real Oxford walking network."""

import math

import pytest

from atlas import routing

pytestmark = pytest.mark.skipif(
    not (routing.PROCESSED / "oxford" / "walk_edges.parquet").exists(),
    reason="walking network not downloaded",
)


def test_stairs_are_never_used_and_steep_costs_more():
    base = {"steps": False, "highway": "footway", "footway": "sidewalk", "grade": 2.0}
    assert routing.penalty({**base, "steps": True}) == math.inf
    assert (
        routing.penalty({**base, "grade": 9.0})
        > routing.penalty({**base, "grade": 6.0})
        > routing.penalty(base)
    )
    assert routing.penalty(
        {**base, "highway": "residential", "footway": None, "sidewalk": "no"}
    ) > routing.penalty(base)


def test_route_king_library_avoids_stairs():
    r = routing.route(
        "oxford", 39.5079, -84.7368, 39.5088, -84.7345
    )  # McGuffey Dr stop -> King Library east door
    assert r is not None and r["steps"] == 0
    assert r["length_feet"] >= r["shortest"]["length_feet"]
    assert r["directions"] and all(d.endswith(".") for d in r["directions"])


def test_far_points_return_none():
    assert routing.route("oxford", 39.0, -84.0, 39.5088, -84.7345) is None


@pytest.mark.parametrize(
    ("a", "b", "word"),
    [
        (0, 10, "continue"),
        (0, 90, "turn right"),
        (0, 270, "turn left"),
        (0, 45, "bear right"),
        (0, 180, "turn around"),
    ],
)
def test_turns(a, b, word):
    assert routing._turn(a, b) == word


def test_crossing_words_and_counts():
    assert routing._crossing_words({"signals": True, "audible": True, "tactile": True}) == (
        "Cross at the traffic signal",
        "audible signal; tactile paving at the curb",
    )
    assert routing._crossing_words({"kind": "unmarked"})[0] == "Cross at an unmarked crossing"
    es = [
        {"footway": "crossing", "highway": "footway", "signals": True, "sound": "yes"},
        {"footway": "crossing", "highway": "footway", "signals": True},  # same crossing, second piece
        {"footway": "sidewalk", "highway": "footway"},
        {"footway": "crossing", "highway": "footway", "crossing": "unmarked"},
    ]
    c = routing._crossing_counts(es)
    assert (c["total"], c["signals"], c["audible"], c["unmarked_or_unknown"]) == (2, 1, 1, 1)


def test_blind_profile_prefers_signals():
    assert routing.blind_penalty({"footway": "crossing", "crossing": "unmarked"}) > routing.blind_penalty(
        {"footway": "crossing", "signals": True}
    )
    assert routing.blind_penalty({"footway": "sidewalk"}) == 1.0
