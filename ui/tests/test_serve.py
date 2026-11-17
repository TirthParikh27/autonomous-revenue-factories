"""The server only answers this computer, and the one thing it can change is a factory's own STOP file."""
import json
import threading
import urllib.error
import urllib.request

import pytest

from ui import serve


@pytest.fixture
def root(tmp_path):
    (tmp_path / "factories" / "a-consumer-apps" / "state").mkdir(parents=True)
    (tmp_path / "factories" / "_shared").mkdir()
    return tmp_path


@pytest.fixture
def call(root):
    httpd = serve.server(root, 0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    port = httpd.server_address[1]

    def call(path, body=None, headers=None):
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}{path}", data=None if body is None else body.encode(),
            headers={"Content-Type": "application/json", **(headers or {})} if body is not None else headers or {},
        )
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, response.read().decode()
        except urllib.error.HTTPError as err:
            return err.code, err.read().decode()

    yield call
    httpd.shutdown()
    httpd.server_close()


def test_off_writes_the_stop_file_and_on_removes_only_that_one(root):
    folder = root / "factories" / "a-consumer-apps"
    serve.set_power(root, "a-consumer-apps", False)
    first = (folder / "STOP").read_text()
    assert first.startswith("Turned off in the UI at ")
    serve.set_power(root, "a-consumer-apps", False)       # already off: the first note is kept
    assert (folder / "STOP").read_text() == first

    (folder / "state" / "STOP").write_text("three failures\n")
    (root / "STOP").write_text("everything\n")
    serve.set_power(root, "a-consumer-apps", True)
    assert not (folder / "STOP").exists()
    assert (folder / "state" / "STOP").exists() and (root / "STOP").exists()   # stops the UI did not write stay
    serve.set_power(root, "a-consumer-apps", True)        # already on


def test_on_never_removes_a_stop_the_ui_did_not_write(root, call):
    """After three failed runs the wrapper writes this same file. Only a person who has read it may remove it."""
    stop = root / "factories" / "a-consumer-apps" / "STOP"
    stop.write_text("RUN-3: three failed runs in a row\n")
    with pytest.raises(PermissionError, match="factories/a-consumer-apps/STOP"):
        serve.set_power(root, "a-consumer-apps", True)
    status, body = call("/api/factories/a-consumer-apps/power", '{"on": true}')
    assert status == 409 and "by hand" in json.loads(body)["error"]
    assert stop.read_text() == "RUN-3: three failed runs in a row\n"
    serve.set_power(root, "a-consumer-apps", False)       # off leaves the wrapper's note as it is
    assert stop.read_text() == "RUN-3: three failed runs in a row\n"


@pytest.mark.parametrize("name", ["", "nope", "..", "../factories/a-consumer-apps", "a-consumer-apps/state", "_shared", "."])
def test_only_a_real_factory_can_be_switched(root, name):
    with pytest.raises(LookupError):
        serve.set_power(root, name, False)
    assert not list(root.rglob("STOP"))


def test_the_pages_and_the_data_are_served(call):
    status, body = call("/api/data?x=1")
    assert status == 200 and [f["id"] for f in json.loads(body)["factories"]] == ["a-consumer-apps"]
    for page in ("/board.html", "/live.html", "/app.js"):
        assert call(page)[0] == 200
    assert call("/../serve.py")[0] == 404


def test_the_switch_over_http(call, root):
    stop = root / "factories" / "a-consumer-apps" / "STOP"
    status, body = call("/api/factories/a-consumer-apps/power", '{"on": false}')
    assert status == 200 and stop.exists() and json.loads(body)["factories"][0]["on"] is False
    status, body = call("/api/factories/a-consumer-apps/power", '{"on": true}')
    assert status == 200 and not stop.exists() and json.loads(body)["factories"][0]["on"] is True


@pytest.mark.parametrize("path, body, headers, status", [
    ("/api/factories/nope/power", '{"on": false}', None, 404),
    ("/api/factories/a-consumer-apps/other", '{"on": false}', None, 404),
    ("/api/factories/a-consumer-apps/power", '{"on": "yes"}', None, 400),
    ("/api/factories/a-consumer-apps/power", "not json", None, 400),
    ("/api/factories/a-consumer-apps/power", "[]", None, 400),
    ("/api/factories/a-consumer-apps/power", "{}", None, 400),
    # what another site's page could send: a form post, or a request under its own name
    ("/api/factories/a-consumer-apps/power", '{"on": false}', {"Content-Type": "text/plain"}, 403),
    ("/api/factories/a-consumer-apps/power", '{"on": false}', {"Host": "evil.example"}, 403),
])
def test_a_bad_request_changes_nothing(call, root, path, body, headers, status):
    assert call(path, body, headers)[0] == status
    assert not list(root.rglob("STOP"))


def test_reads_are_refused_under_another_name_too(call):
    assert call("/api/data", headers={"Host": "evil.example"})[0] == 403
    assert call("/board.html", headers={"Host": "evil.example:80"})[0] == 403
    assert call("/api/data", headers={"Host": "localhost:1"})[0] == 200


def test_a_broken_state_file_is_reported_by_name(call, root):
    items = root / "factories" / "a-consumer-apps" / "state" / "items"
    items.mkdir()
    (items / "bad.json").write_text("{")
    status, body = call("/api/data")
    assert status == 500 and "bad.json" in json.loads(body)["error"]


def test_dump_prints_the_data(root, capsys):
    assert serve.main(["--dump", "--root", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["factories"][0]["id"] == "a-consumer-apps"


def test_a_folder_without_factories_is_refused(tmp_path, capsys):
    with pytest.raises(SystemExit):
        serve.main(["--root", str(tmp_path)])
    assert "has no factories/ folder" in capsys.readouterr().err


def test_main_serves_until_interrupted(root, monkeypatch, capsys):
    def interrupted(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(serve.ThreadingHTTPServer, "serve_forever", interrupted)
    assert serve.main(["--root", str(root), "--port", "0"]) == 0
    assert "Factory UI: http://127.0.0.1:" in capsys.readouterr().out
