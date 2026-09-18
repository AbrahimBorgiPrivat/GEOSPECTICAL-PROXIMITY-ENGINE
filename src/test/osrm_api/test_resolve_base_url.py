import pytest

from libraries.classes.osrm_api import OSRMClient


@pytest.mark.parametrize(
    ("profile", "expected"),
    [
        ("foot", "http://localhost:5000"),
        ("car", "http://localhost:5001"),
        ("bicycle", "http://localhost:5002"),
    ],
)
def test_resolve_base_url_uses_docker_profile_ports(profile, expected):
    client = OSRMClient(base_url="local", profile=profile)

    assert client.base_url == expected
    assert client._resolve_base_url(profile) == expected


def test_resolve_base_url_uses_profile_environment_override(monkeypatch):
    monkeypatch.setenv("OSRM_CAR_URL", "http://car.example/")
    client = OSRMClient(base_url="local", profile="car")

    assert client.base_url == "http://car.example"


def test_remote_base_url_is_normalized_without_local_profile_validation():
    client = OSRMClient(base_url="http://osrm.example///", profile="car")

    assert client.base_url == "http://osrm.example"
