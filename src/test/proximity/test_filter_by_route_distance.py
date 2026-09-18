from libraries.algoritm.proximity import filter_by_route_distance


def test_filter_by_route_distance_keeps_distance_on_radius_boundary():
    candidates = [(0, 0, 90.0), (0, 1, 80.0), (1, 0, 70.0)]
    distances = {(0, 0): 100.0, (0, 1): 101.0, (1, 0): 50.0}

    matches = filter_by_route_distance(candidates, distances, 100)

    assert matches == [
        {"source_index": 0, "target_index": 0, "geodist": 90.0, "dist": 100.0},
        {"source_index": 1, "target_index": 0, "geodist": 70.0, "dist": 50.0},
    ]


def test_filter_by_route_distance_returns_empty_without_route_matches():
    assert filter_by_route_distance([(0, 0, 50.0)], {}, 100) == []
