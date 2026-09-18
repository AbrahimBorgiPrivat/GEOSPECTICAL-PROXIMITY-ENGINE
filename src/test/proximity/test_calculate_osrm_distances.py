import numpy as np

from libraries.algoritm.proximity import calculate_osrm_distances


SOURCES = [{"lon": 12.0, "lat": 55.0}, {"lon": 12.1, "lat": 55.1}]
TARGETS = [
    {"lon": 12.001, "lat": 55.0, "weight": 1},
    {"lon": 12.101, "lat": 55.1, "weight": 2},
]


class FakeOSRMClient:
    def __init__(self):
        self.calls = []

    def table_between_chunked(self, sources, targets, **kwargs):
        self.calls.append((sources, targets, kwargs))
        return np.array([[123.0]])


def test_calculate_osrm_distances_only_requests_candidate_pairs():
    client = FakeOSRMClient()
    candidates = [(1, 0, 50.0)]

    distances = calculate_osrm_distances(SOURCES, TARGETS, candidates, client)

    assert distances == {(1, 0): 123.0}
    assert len(client.calls) == 1
    sources, targets, kwargs = client.calls[0]
    assert sources == [SOURCES[1]]
    assert targets == [TARGETS[0]]
    assert kwargs["annotations"] == "distance"


def test_calculate_osrm_distances_uses_one_chunked_call_for_multiple_targets():
    class MultiTargetClient:
        def __init__(self):
            self.calls = 0

        def table_between_chunked(self, sources, targets, **kwargs):
            self.calls += 1
            return np.array([[10.0, 20.0, 30.0]])

    client = MultiTargetClient()
    candidates = [(0, 0, 1.0), (0, 1, 2.0), (0, 2, 3.0)]
    targets = TARGETS + [{"lon": 12.2, "lat": 55.2, "weight": 3}]

    distances = calculate_osrm_distances(SOURCES, targets, candidates, client)

    assert distances == {(0, 0): 10.0, (0, 1): 20.0, (0, 2): 30.0}
    assert client.calls == 1


def test_calculate_osrm_distances_makes_no_call_without_candidates():
    client = FakeOSRMClient()

    assert calculate_osrm_distances(SOURCES, TARGETS, [], client) == {}
    assert client.calls == []
