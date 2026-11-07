"""Rule-based wheelchair-relevance signal for (attribute, value) pairs.

Rules are deliberately simple and grounded in the 2010 ADA Standards so they can be
stated in a methods section and validated against field audits:
  running slope <= 5% (1:20) accessible route, <= 8.33% (1:12) ramp   (ADA 403.3, 405.2)
  clear width >= 0.915 m (36 in), >= 1.525 m (60 in) passing space    (ADA 403.5)
"""
from __future__ import annotations

import math
import re

SUPPORTS, LIMITED, BARRIER, UNKNOWN = "supports", "limited", "barrier", "unknown"

_TABLES: dict[str, dict[str, str]] = {
    "yesno": {"yes": SUPPORTS, "designated": SUPPORTS, "limited": LIMITED, "assisted": LIMITED,
              "no": BARRIER},
    "surface": {
        **dict.fromkeys(["asphalt", "concrete", "concrete:plates", "concrete:lanes", "paved",
                         "paving_stones", "metal", "wood", "rubber", "tartan", "acrylic"], SUPPORTS),
        **dict.fromkeys(["compacted", "fine_gravel", "bricks", "brick"], LIMITED),
        **dict.fromkeys(["gravel", "cobblestone", "sett", "unhewn_cobblestone", "pebblestone", "dirt",
                         "ground", "earth", "grass", "sand", "mud", "woodchips", "rock",
                         "stepping_stones"], BARRIER),
    },
    "smoothness": {"excellent": SUPPORTS, "good": SUPPORTS, "intermediate": LIMITED,
                   **dict.fromkeys(["bad", "very_bad", "horrible", "very_horrible", "impassable"],
                                   BARRIER)},
    # kerb=yes means "a kerb of unspecified height" -> unknown
    "kerb": {"flush": SUPPORTS, "lowered": SUPPORTS, "no": SUPPORTS, "rolled": LIMITED,
             "raised": BARRIER},
    "barrier": {**dict.fromkeys(["bollard", "kerb", "step", "stile", "turnstile", "kissing_gate",
                                 "full-height_turnstile", "block"], BARRIER),
                **dict.fromkeys(["gate", "lift_gate", "swing_gate", "cycle_barrier"], LIMITED)},
    # GTFS wheelchair_boarding: 0/empty no info, 1 possible, 2 not possible
    "wheelchair_boarding": {"1": SUPPORTS, "2": BARRIER},
}

_ATTRIBUTE_TABLE = {
    "wheelchair": "yesno", "toilets:wheelchair": "yesno", "entrance:wheelchair": "yesno",
    "ramp:wheelchair": "yesno", "automatic_door": "yesno", "elevator": "yesno",
    "kerb": "kerb", "barrier": "barrier", "wheelchair_boarding": "wheelchair_boarding",
}

_NUM = re.compile(r"^-?(\d*\.?\d+)\s*(%|°)?$")


def incline(value: str) -> str:
    v = value.strip().lower()
    if v in {"up", "down", "yes"}:
        return LIMITED  # sloped, magnitude unknown
    m = _NUM.match(v)
    if not m:
        return UNKNOWN
    pct = float(m.group(1))  # bare number = percent (OSM convention)
    if m.group(2) == "°":
        pct = math.tan(math.radians(pct)) * 100
    return SUPPORTS if pct <= 5.0 else LIMITED if pct <= 8.33 else BARRIER


def width(value: str) -> str:
    m = re.match(r"^(\d*\.?\d+)\s*m?$", value.strip())
    if not m:
        return UNKNOWN
    w = float(m.group(1))
    return SUPPORTS if w >= 1.525 else LIMITED if w >= 0.915 else BARRIER


def signal(attribute: str, value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return UNKNOWN
    v = str(value).strip().lower()
    if attribute in _ATTRIBUTE_TABLE:
        return _TABLES[_ATTRIBUTE_TABLE[attribute]].get(v, UNKNOWN)
    if attribute.endswith("surface"):
        return _TABLES["surface"].get(v, UNKNOWN)
    if attribute.endswith("smoothness"):
        return _TABLES["smoothness"].get(v, UNKNOWN)
    if attribute.endswith("incline"):
        return incline(v)
    if attribute.endswith("width"):
        return width(v)
    if attribute == "highway":
        return BARRIER if v == "steps" else UNKNOWN
    if attribute == "step_count":
        return SUPPORTS if v == "0" else BARRIER
    return UNKNOWN
