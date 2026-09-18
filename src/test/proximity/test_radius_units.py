import numpy as np

from libraries.algoritm.algoritm import run_proximity
from libraries.algoritm.proximity import radius_to_meters, resolve_speed_mps


def test_profile_speeds_are_used_for_time_radius_conversion():
    assert resolve_speed_mps("foot") == 1.4
    assert resolve_speed_mps("bicycle") == 5.6
    assert resolve_speed_mps("car") == 13.9
    assert radius_to_meters(60, "duration", profile="foot") == 84.0


def test_explicit_speed_overrides_profile_default():
    assert radius_to_meters(60, "duration", profile="foot", speed_mps=2.0) == 120.0


def test_duration_radius_uses_osrm_durations_and_returns_seconds():
    class FakeOSRMClient:
        def __init__(self):
            self.annotations = []

        def table_between_chunked(self, sources, targets, **kwargs):
            self.annotations.append(kwargs["annotations"])
            return np.array([[45.0]])

    client = FakeOSRMClient()
    distance_matrix, relations, summary = run_proximity(
        sources=[{"lon": 12.0, "lat": 55.0}],
        targets=[{"lon": 12.0005, "lat": 55.0, "weight": 3}],
        radius=60,
        distance_unit="duration",
        profile="foot",
        osrm_client=client,
    )

    assert client.annotations == ["duration"]
    assert np.array_equal(distance_matrix, [[45.0]])
    assert relations[0]["dist"] == 45.0
    assert summary["number_of_targets"] == 1
