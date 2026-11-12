import pytest

from atlas.signals import BARRIER, LIMITED, SUPPORTS, UNKNOWN, signal


@pytest.mark.parametrize(
    ("attr", "value", "expected"),
    [
        ("wheelchair", "yes", SUPPORTS),
        ("wheelchair", "limited", LIMITED),
        ("wheelchair", "no", BARRIER),
        ("wheelchair", "maybe", UNKNOWN),
        ("wheelchair", None, UNKNOWN),
        ("surface", "asphalt", SUPPORTS),
        ("sidewalk:both:surface", "gravel", BARRIER),
        ("surface", "bricks", LIMITED),
        ("incline", "4%", SUPPORTS),
        ("incline", "4", SUPPORTS),
        ("incline", ".5", SUPPORTS),
        ("incline", "-7%", LIMITED),
        ("incline", "12%", BARRIER),
        ("incline", "3°", LIMITED),
        ("incline", "up", LIMITED),
        ("incline", "steep", UNKNOWN),
        ("width", "2", SUPPORTS),
        ("width", "1.2 m", LIMITED),
        ("width", "0.8", BARRIER),
        ("kerb", "lowered", SUPPORTS),
        ("kerb", "raised", BARRIER),
        ("kerb", "yes", UNKNOWN),
        ("highway", "steps", BARRIER),
        ("highway", "footway", UNKNOWN),
        ("step_count", "0", SUPPORTS),
        ("step_count", "3", BARRIER),
        ("wheelchair_boarding", "1", SUPPORTS),
        ("wheelchair_boarding", "2", BARRIER),
        ("wheelchair_boarding", "0", UNKNOWN),
    ],
)
def test_signal(attr, value, expected):
    assert signal(attr, value) == expected
