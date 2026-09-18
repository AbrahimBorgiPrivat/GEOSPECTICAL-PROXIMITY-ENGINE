import numpy as np
import pytest

from libraries.algoritm.proximity import find_proximity


SOURCES = [
    {"lon": 12.0, "lat": 55.0},
    {"lon": 12.001, "lat": 55.0},
]
TARGETS = [{"lon": 12.0005, "lat": 55.0, "weight": 6}]


class FakeOSRMClient:
    def __init__(self, distance):
        self.distance = distance
        self.calls = []

    def table_between_chunked(self, sources, targets, **kwargs):
        self.calls.append((sources, targets, kwargs))
        return np.array([[self.distance]])


def test_find_proximity_returns_distances_relations_and_summary():
    client = FakeOSRMClient(distance=40)

    matrix, relations, summary = find_proximity(
        SOURCES, TARGETS, radius=100, osrm_client=client
    )

    assert matrix.shape == (2, 1)
    assert np.allclose(matrix, [[40], [40]])
    assert len(relations) == 2
    assert relations[0]["source_index"] == 0
    assert relations[0]["target_index"] == 0
    assert all(relation["weight"] == 6 for relation in relations)
    assert summary == {
        "number_of_sources": 2,
        "number_of_targets": 2,
        "number_of_unique_targets": 1,
        "sum_of_weight": 12.0,
        "unique_sum_of_weight": 6.0,
    }
    assert len(client.calls) == 2


def test_find_proximity_filters_out_route_distance_beyond_radius():
    client = FakeOSRMClient(distance=101)

    matrix, relations, summary = find_proximity(
        [SOURCES[0]], TARGETS, radius=100, osrm_client=client
    )

    assert np.isnan(matrix[0, 0])
    assert relations == []
    assert summary["number_of_targets"] == 0


@pytest.mark.parametrize(
    "targets",
    [
        [{"lon": 12.0, "lat": 55.0}],
        [{"lon": 12.0, "lat": 55.0, "weight": -1}],
    ],
)
def test_find_proximity_rejects_missing_or_invalid_target_weight(targets):
    with pytest.raises(ValueError):
        find_proximity(SOURCES[:1], targets, radius=100, osrm_client=FakeOSRMClient(1))
