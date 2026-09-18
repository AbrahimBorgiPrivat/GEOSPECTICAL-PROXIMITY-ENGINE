import numpy as np

from libraries.algoritm.algoritm import run_proximity


class FakeOSRMClient:
    def table_between_chunked(self, sources, targets, **kwargs):
        return np.array([[75.0]])


def test_run_proximity_returns_d_relations_and_summary():
    sources = [
        {"lon": 12.0, "lat": 55.0},
        {"lon": 12.001, "lat": 55.0},
    ]
    targets = [{"lon": 12.0005, "lat": 55.0, "weight": 6}]

    distance_matrix, relations, summary = run_proximity(
        sources, targets, radius=100, osrm_client=FakeOSRMClient()
    )

    assert np.allclose(distance_matrix, [[75.0], [75.0]])
    assert relations[0]["source_index"] == 0
    assert relations[0]["target_index"] == 0
    assert relations[0]["source_lon"] == 12.0
    assert relations[0]["target_lat"] == 55.0
    assert relations[0]["dist"] == 75.0
    assert relations[0]["geodist"] <= 100
    assert summary == {
        "number_of_sources": 2,
        "number_of_targets": 2,
        "number_of_unique_targets": 1,
        "sum_of_weight": 12.0,
        "unique_sum_of_weight": 6.0,
    }
