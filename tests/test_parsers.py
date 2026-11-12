"""Parsers that turn saved pages into dated events and listings. Each test uses text shaped exactly
like the saved page, so a site redesign that breaks the parser fails here, not on the live map."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


perf = load("extract_access_performances")
rest = load("extract_enjoyoxford_restaurants")


def doc(text: str, url: str = "https://example.org/x", title: str = "") -> SimpleNamespace:
    return SimpleNamespace(doc_id="test:abc", text=text, url=url, title=title)


PLAYHOUSE = """Sensory Friendly/​Relaxed Performances
Our sensory-friendly/relaxed performance is designed for anyone.
26-27 season performance dates:
A Christmas Carol
Sat. Nov 28, 12 p.m.
BUY TICKETS & LEARN MORE
Audio-Described Performances
This service is free. Please see dates below.
26-27 season performance dates:
Heist
Sat., Oct. 3 at 2 p.m.
Rope
Sat., May 15 at 2 p.m.
Signed ASL Performances
Signed performances for those with hearing impairments are offered for designated performances.
26-27 season performance dates:
Heist
Sun., Oct. 4 at 2 p.m.
Hearing Enhancement System
Moe and Jack's Place"""


def test_playhouse_sections_years_and_times():
    ev = {(e["title"], e["start"], tuple(e["access"])) for e in perf.playhouse(doc(PLAYHOUSE))}
    assert ev == {
        ("A Christmas Carol", "2026-11-28T12:00", ("sensory_friendly",)),
        ("Heist", "2026-10-03T14:00", ("audio_description",)),
        ("Rope", "2027-05-15T14:00", ("audio_description",)),  # spring belongs to the next calendar year
        ("Heist", "2026-10-04T14:00", ("asl",)),
    }


def test_playhouse_stops_at_next_heading():
    assert not any(e["title"].startswith("Moe") for e in perf.playhouse(doc(PLAYHOUSE)))


TCT = """Which MainStage performances are signed & audio described?
Dr. Seuss’s How the Grinch Stole Christmas! The Musical
– Saturday, December 12 at 2 PM
Peter Pan JR.
– Saturday, February 27 at 2 PM
School performances on Thursdays at 1 PM are signed.
2026–2027 season at the Emery Theater."""


def test_childrens_theatre_both_services():
    ev = perf.childrens_theatre(doc(TCT))
    assert [(e["start"], e["access"]) for e in ev] == [
        ("2026-12-12T14:00", ["asl", "audio_description"]),
        ("2027-02-27T14:00", ["asl", "audio_description"]),
    ]


SHAKES = """subscribe and save
Fri - Mar 5, 2027 - 7:30 PM
Opening Night | Audio Description Service Available
Book
Sat - Mar 6, 2027 - 7:30 PM
Book
Sun - Mar 28, 2027 - 2:00 PM
Post-Show Q&A with Cast | Sign Language Interpreted
Book"""


def test_shakespeare_labels_on_shared_line():
    ev = perf.shakespeare(doc(SHAKES, title="Hamlet | Cincy Shakes"))
    assert [(e["title"], e["start"], e["access"]) for e in ev] == [
        ("Hamlet", "2027-03-05T19:30", ["audio_description"]),
        ("Hamlet", "2027-03-28T14:00", ["asl"]),  # the plain Mar 6 show is not included
    ]
    assert (
        ev[0]["quote"] == "Fri - Mar 5, 2027 - 7:30 PM\nOpening Night | Audio Description Service Available"
    )


@pytest.mark.parametrize(
    ("h", "m", "ap", "out"),
    [
        ("2", None, "p", "14:00"),
        ("12", None, "p", "12:00"),
        ("12", "30", "a", "00:30"),
        ("7", "30", "P", "19:30"),
    ],
)
def test_clock(h, m, ap, out):
    assert perf.clock(h, m, ap) == out


def test_restaurant_fields():
    lines = [
        "Features:",
        "Outdoor Patio, Wheelchair Accessible",
        "Restaurant Name:",
        "Kofenya",
        "Address:",
        "38 West High Street",
    ]
    assert rest.field(lines, "Restaurant Name") == "Kofenya"
    assert rest.field(lines, "Address") == "38 West High Street"
    assert rest.field(lines, "Phone Number") is None
