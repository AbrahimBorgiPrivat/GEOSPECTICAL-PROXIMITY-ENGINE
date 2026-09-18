import pytest

from libraries.algoritm.proximity import geographical_distance


def test_geographical_distance_is_zero_for_same_coordinates():
    location = {"lon": 12.5683, "lat": 55.6761}

    assert geographical_distance(location, location) == pytest.approx(0)


def test_geographical_distance_is_in_metres_with_reasonable_tolerance():
    distance = geographical_distance(
        {"lon": 12.5683, "lat": 55.6761},
        {"lon": 12.5800, "lat": 55.6800},
    )

    assert distance == pytest.approx(852, rel=0.01)


@pytest.mark.parametrize(
    "location",
    [
        {"lon": 12.0},
        {"lat": 55.0},
        {"lon": "bad", "lat": 55.0},
        {"lon": float("nan"), "lat": 55.0},
        {"lon": 181.0, "lat": 55.0},
    ],
)
def test_geographical_distance_rejects_invalid_coordinates(location):
    with pytest.raises(ValueError):
        geographical_distance(location, {"lon": 12.0, "lat": 55.0})
