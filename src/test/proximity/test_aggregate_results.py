from libraries.algoritm.proximity import aggregate_results


SOURCES = [{"lon": 1.0, "lat": 2.0}, {"lon": 3.0, "lat": 4.0}]
TARGETS = [
    {"lon": 5.0, "lat": 6.0, "weight": 6},
    {"lon": 7.0, "lat": 8.0, "weight": 2},
]


def test_aggregate_results_counts_duplicate_target_matches_correctly():
    matches = [
        {"source_index": 0, "target_index": 0},
        {"source_index": 1, "target_index": 0},
        {"source_index": 1, "target_index": 1},
    ]

    assert aggregate_results(SOURCES, TARGETS, matches) == {
        "number_of_sources": 2,
        "number_of_targets": 3,
        "number_of_unique_targets": 2,
        "sum_of_weight": 14.0,
        "unique_sum_of_weight": 8.0,
    }


def test_aggregate_results_handles_no_matches():
    assert aggregate_results(SOURCES, TARGETS, []) == {
        "number_of_sources": 2,
        "number_of_targets": 0,
        "number_of_unique_targets": 0,
        "sum_of_weight": 0,
        "unique_sum_of_weight": 0,
    }
