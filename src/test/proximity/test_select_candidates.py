import pytest

from libraries.algoritm.proximity import select_candidates


SOURCE = {"lon": 12.0, "lat": 55.0}
TARGET_NEAR = {"lon": 12.001, "lat": 55.0, "weight": 2}
TARGET_FAR = {"lon": 13.0, "lat": 55.0, "weight": 4}


def test_select_candidates_keeps_only_targets_within_radius():
    candidates = select_candidates([SOURCE], [TARGET_NEAR, TARGET_FAR], 100)

    assert len(candidates) == 1
    assert candidates[0][0:2] == (0, 0)
    assert candidates[0][2] <= 100


def test_select_candidates_returns_empty_when_no_target_is_close():
    assert select_candidates([SOURCE], [TARGET_FAR], 100) == []


def test_select_candidates_includes_pair_on_radius_boundary():
    boundary = {"lon": 12.001, "lat": 55.0, "weight": 1}
    distance = select_candidates([SOURCE], [boundary], 1000)[0][2]

    assert select_candidates([SOURCE], [boundary], distance) == [(0, 0, distance)]


@pytest.mark.parametrize("radius", [-1, "bad"])
def test_select_candidates_rejects_invalid_radius(radius):
    with pytest.raises(ValueError):
        select_candidates([SOURCE], [TARGET_NEAR], radius)
