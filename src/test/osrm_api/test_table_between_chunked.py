import numpy as np
import pytest

from libraries.classes.osrm_api import OSRMClient


def location(identifier):
    return {"id": identifier, "lon": 12.0 + identifier, "lat": 55.0}


def test_table_between_chunked_places_all_blocks_and_indices(monkeypatch):
    calls = []

    def fake_table(locations, **kwargs):
        calls.append((locations, kwargs))
        return {
            "distances": [
                [
                    locations[source]["id"] * 10
                    + locations[destination]["id"]
                    for destination in kwargs["destinations"]
                ]
                for source in kwargs["sources"]
            ]
        }

    client = OSRMClient(base_url="http://osrm.example", profile="car")
    monkeypatch.setattr(client, "table", fake_table)
    sources = [location(0), location(1), location(2)]
    targets = [location(10), location(11), location(12)]

    result = client.table_between_chunked(sources, targets, chunk_size=2)

    assert np.array_equal(result, [[10, 11, 12], [20, 21, 22], [30, 31, 32]])
    assert len(calls) == 4
    for locations, kwargs in calls:
        source_count = kwargs["destinations"][0]
        assert kwargs["sources"] == list(range(source_count))
        assert kwargs["destinations"] == list(
            range(source_count, len(locations))
        )


def test_table_between_chunked_handles_empty_inputs_without_requests(monkeypatch):
    client = OSRMClient(base_url="http://osrm.example", profile="car")
    monkeypatch.setattr(
        client,
        "table",
        lambda *args, **kwargs: pytest.fail("No request expected"),
    )

    assert client.table_between_chunked([], [location(1)]).shape == (0, 1)
    assert client.table_between_chunked([location(1)], []).shape == (1, 0)


def test_table_between_chunked_preserves_none_as_nan(monkeypatch):
    client = OSRMClient(base_url="http://osrm.example", profile="car")
    monkeypatch.setattr(
        client,
        "table",
        lambda *args, **kwargs: {"distances": [[None]]},
    )

    result = client.table_between_chunked([location(0)], [location(1)])

    assert np.isnan(result[0, 0])


def test_table_between_chunked_propagates_api_failures(monkeypatch):
    def failing_table(*args, **kwargs):
        raise RuntimeError("OSRM unavailable")

    monkeypatch.setattr(client := OSRMClient(base_url="http://osrm.example"), "table", failing_table)

    with pytest.raises(RuntimeError, match="OSRM unavailable"):
        client.table_between_chunked([location(0)], [location(1)])


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_table_between_chunked_rejects_invalid_chunk_size(chunk_size):
    client = OSRMClient(base_url="http://osrm.example")

    with pytest.raises(ValueError):
        client.table_between_chunked([location(0)], [location(1)], chunk_size=chunk_size)


def test_table_between_chunked_rejects_impossible_coordinate_limit():
    client = OSRMClient(base_url="http://osrm.example")

    with pytest.raises(ValueError):
        client.table_between_chunked(
            [location(0)], [location(1)], max_coordinates_per_request=1
        )
