from libraries.classes.osrm_api import OSRMClient


def test_resolve_profile_uses_client_profile_when_not_provided():
    client = OSRMClient(base_url="http://osrm.example", profile="CAR")

    assert client._resolve_profile(None) == "car"


def test_resolve_profile_normalizes_profile_name():
    client = OSRMClient(base_url="http://osrm.example")

    assert client._resolve_profile("BICYCLE") == "bicycle"


def test_resolve_profile_rejects_unknown_local_profile():
    client = OSRMClient(base_url="local", profile="foot")

    try:
        client._resolve_base_url("unknown")
    except ValueError as error:
        assert "unknown" in str(error)
    else:
        raise AssertionError("Unknown local profile should raise ValueError")
