import requests

from libraries.classes.osrm_api import OSRMClient


LOCATIONS = [
    {"lon": 12.5683, "lat": 55.6761},
    {"lon": 12.5800, "lat": 55.6800},
]


class DummyResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"routes": [{"distance": 10.0, "duration": 2.0}]}


def test_route_builds_request_and_returns_payload(monkeypatch):
    calls = []

    def fake_get(url, params=None):
        calls.append((url, params))
        return DummyResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    client = OSRMClient(base_url="http://osrm.example/", profile="car")

    result = client.route(LOCATIONS, steps=True, annotations="distance")

    assert result["routes"][0]["distance"] == 10.0
    assert calls[0][0].startswith("http://osrm.example/route/v1/car/")
    assert calls[0][1]["steps"] == "true"
    assert calls[0][1]["annotations"] == "distance"
