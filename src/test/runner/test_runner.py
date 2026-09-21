import json

from libraries.runner import runner


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"summary": {"number_of_targets": 1}}


def test_run_posts_json_request_and_returns_response(tmp_path, monkeypatch):
    input_path = tmp_path / "request.json"
    input_path.write_text(
        json.dumps({"sources": [], "targets": [], "radius": 100}),
        encoding="utf-8",
    )
    captured = {}

    def fake_post(url, *, json, timeout):
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(runner.requests, "post", fake_post)

    result = runner.run(input_path, "http://service.test/proximity")

    assert result == {"summary": {"number_of_targets": 1}}
    assert captured == {
        "url": "http://service.test/proximity",
        "json": {"sources": [], "targets": [], "radius": 100},
        "timeout": 300,
    }
