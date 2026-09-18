from libraries.classes.osrm_api import OSRMClient


def test_resolve_path_profile_returns_supported_profile():
    client = OSRMClient(base_url="http://osrm.example", profile="foot")

    assert client._resolve_path_profile(None) == "foot"
    assert client._resolve_path_profile("CAR") == "car"
    assert client._resolve_path_profile("BICYCLE") == "bicycle"
