# ruff: noqa: E501  (long regex and source text)
"""Sort upcoming Miami University calendar events by how useful they are to the atlas.

Rules were written by Claude (Claude Code session, 2026-11-11) after reading all 176 distinct titles of
the 408 upcoming events. They are explicit so anyone can check or change them; each event records
the rule that classified it. Output: data/extracted/miami_events_classified.jsonl

Classes:
  disability_focused   for or about disabled people (none found in this batch)
  staff_training       accessibility training for staff/faculty (not for visitors)
  public_leisure       open to the public: performances, exhibits, skating, festivals, talks, workshops
  campus_internal      aimed at enrolled students or staff: careers, dining, clubs, study, admin
  calendar_notice      breaks and closures, not events
Plus two flags kept from the description: has_accommodation_statement, captioning_provided.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

RULES = [  # first match wins; (class, regex on title, why)
    ("disability_focused", r"disabilit|adaptive|wheelchair|sensory[- ]friendly|\bASL\b|deaf|blind", "disability words in title"),
    ("staff_training", r"Accessibility Fundamentals", "digital accessibility (Title II) training for staff"),
    ("public_leisure", r"Artist Talk|Attention in the Age of Distraction|Music for Oboe",
     "public talk or performance whose title also contains a campus word"),
    ("calendar_notice", r"Thanksgiving Break|Winter Holiday Break(?! Holiday Skate)", "break notice"),
    ("campus_internal", r"Board of Trustees|Career|Interview|Resume|Info Session|Networking|Mock |CV Workshop|"
                        r"Cram|Study Break|Writing Hours|Teaching and Learning|Commuter Center|Dining|Commons|"
                        r"Pantry|Club|GBM|HSAB|ISSS|SLAM|SLSAM|AIAS|Grad Central|Nav Night|Simulator|"
                        r"Weekly Lift|Get Moving|Model Arab League|Republicans|Self Care|Stress Less|"
                        r"Made to Move|Friendsgiving|Food Night|Education Abroad|Travel 101|PCLS|MiamiEVO|"
                        r"Prompt Like|Cite it Right|Fact or Fiction|Dog Therapy|Pop in with Poppy|Mental Health|"
                        r"Play, Relax|Card Making|Executive Director of MUDEC|New Books at Miami|"
                        r"Thanksgiving Dinner|Throwback|Karaoke|Winter Snowglobes|Black Hair Expo|"
                        r"Charcuterie|Simmer Pot|Magazine Release|Graduate Symposium|Bowling|Sketched Out|Blood Drive|"
                        r"Pet Day|Cozy Crafts|Fashion Switch|Valentine's Crafts|Sticker|Games Night|"
                        r"Art and Wellness|Commencement|Mean Girls|Kevin Singh|OxWee|Mindful Eating|Family Dinner",
     "aimed at students/staff, or campus-only activity"),
    ("public_leisure", r"Recital|Concert|Ensemble|Orchestra|Voices|Steel Band|Theatre|Last Five Years|Dolly|"
                       r"Tartan|Light of Hope|Phony Awards|Skate|Hockey|Ice Skating|Festival|Fest\b|Sparkfest|"
                       r"Expo|Exhibit|Self In Digital Age|Art Wall|Artist Talk|Lecture|Evening with|Poetry|"
                       r"Thane Maynard|Birding|Christmas Traditions|SongFarmers|Creativa|Dan Patch|"
                       r"What.s In Our Food|Glass Blowing|Cyanotypes|Earrings|Felted|Life Drawing|Art Explorers|"
                       r"Makerspace|National Parks|Basketball|Aquarium Trip|Kenwood|Attention|Surveillance|"
                       r"Diplomacy|Speaker|Writing Instruction|Screen Free|Diving Board|Intention, Identity|"
                       r"Physiological|Electric Root|Cavaliers",
     "public performance, exhibit, recreation or talk"),
]


def classify(title: str) -> tuple[str, str]:
    for cls, pattern, why in RULES:
        if re.search(pattern, title, re.I):
            return cls, why
    return "unclassified", "no rule matched"


def main() -> None:
    e = pd.read_parquet(ROOT / "data/processed/oxford/events_ical_oxford.events.parquet")
    e = e[e.start >= "2026-11-11"].copy()
    out = []
    for r in e.itertuples():
        cls, why = classify(r.title)
        out.append({"event_id": r.event_id, "title": r.title.strip(), "start": r.start, "end": r.end,
                    "venue": r.venue, "url": r.url, "class": cls, "rule": why,
                    "has_accommodation_statement": bool(re.search(r"disability-related accommodations", r.description, re.I)),
                    "captioning_provided": bool(re.search(r"captioning will be provided", r.description, re.I)),
                    "region": "oxford", "raw_file": r.raw_file, "classified_by": "rules in scripts/classify_miami_events.py"})
    df = pd.DataFrame(out)
    (ROOT / "data/extracted/miami_events_classified.jsonl").write_text(
        "".join(json.dumps(x) + "\n" for x in out))
    print(df["class"].value_counts().to_string())
    print("with accommodation statement:", int(df.has_accommodation_statement.sum()),
          "| captioning provided:", int(df.captioning_provided.sum()))
    un = df[df["class"] == "unclassified"].title.unique()
    if len(un):
        print("UNCLASSIFIED:", list(un))


if __name__ == "__main__":
    main()
