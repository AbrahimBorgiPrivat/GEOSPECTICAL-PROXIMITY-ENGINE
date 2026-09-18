import numpy as np

from libraries.classes.osrm_api import OSRMClient


def test_table_chunked_places_mocked_blocks_correctly(monkeypatch):
    locations = [{"lon": float(index), "lat": 55.0} for index in range(3)]
    client = OSRMClient(base_url="http://osrm.example", profile="car")

    def fake_table(block_locations, **kwargs):
        return {
            "distances": [
                [
                    float(
                        block_locations[source]["lon"] * 10
                        + block_locations[destination]["lon"]
                    )
                    for destination in kwargs["destinations"]
                ]
                for source in kwargs["sources"]
            ]
        }

    monkeypatch.setattr(client, "table", fake_table)
    result = client.table_chunked(locations, chunk_size=2)

    assert np.array_equal(result, [[0, 1, 2], [10, 11, 12], [20, 21, 22]])
