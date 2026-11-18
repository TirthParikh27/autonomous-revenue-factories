#!/usr/bin/env python3
"""Serves Keiretsu, the factory console, on this computer only.

    python ui/serve.py [--root PATH] [--port 8765]     then open http://127.0.0.1:8765
    python ui/serve.py --dump [--root PATH]            print what the pages would show, and exit

--root is a checkout that holds factories/. Run state lives on the factory-state branch, so point it there.
The only thing the UI can change is a factory's own STOP file, which is its off switch.
"""
import argparse
import datetime as dt
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ui import data  # noqa: E402

STATIC = Path(__file__).with_name("static")
HOSTS = ("127.0.0.1", "localhost")
OFF_NOTE = "Turned off in the UI"


def set_power(root: Path, factory_id: str, on: bool) -> None:
    """Off writes factories/<id>/STOP, which every run checks before it starts.

    On removes that file only if this UI wrote it. A STOP written by anything else, such as the run wrapper
    after three failed runs, stays until a person has read it and removed it by hand.
    """
    folder = root / "factories" / factory_id
    if not factory_id or Path(factory_id).name != factory_id or factory_id.startswith((".", "_")) or not folder.is_dir():
        raise LookupError(f"no factory named {factory_id!r}")
    stop = folder / "STOP"
    if on and stop.exists():
        if not stop.read_text().startswith(OFF_NOTE):
            raise PermissionError(f"{stop.relative_to(root).as_posix()} was not written by this UI. Read it, then remove it by hand.")
        stop.unlink()
    elif not on and not stop.exists():
        stop.write_text(f"{OFF_NOTE} at {dt.datetime.now().astimezone().isoformat(timespec='seconds')}\n")


class Handler(SimpleHTTPRequestHandler):
    root: Path

    def reply(self, status: int, body: dict) -> None:
        raw = json.dumps(body, allow_nan=False).encode()      # NaN is not JSON a browser can read
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def local_only(self) -> bool:
        """Refuse a request that reached us under another site's name."""
        return self.headers.get("Host", "").rsplit(":", 1)[0] in HOSTS

    def do_GET(self) -> None:
        if not self.local_only():
            return self.reply(403, {"error": "this UI only answers on 127.0.0.1"})
        if self.path.split("?")[0] != "/api/data":
            return super().do_GET()
        self.send_data()

    def send_data(self) -> None:
        try:
            self.reply(200, data.build(self.root))
        except (ValueError, OSError) as err:      # a broken state file: say which, do not guess
            self.reply(500, {"error": f"Could not read the factory files. {err}"})

    def do_POST(self) -> None:
        parts = self.path.strip("/").split("/")
        # A JSON content type cannot be sent by another site's page without our permission, which we never give.
        if not self.local_only() or self.headers.get("Content-Type") != "application/json":
            return self.reply(403, {"error": "refused"})
        if len(parts) != 4 or parts[:2] != ["api", "factories"] or parts[3] != "power":
            return self.reply(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            on = body.get("on") if isinstance(body, dict) else None
            if not isinstance(on, bool):
                raise ValueError('send {"on": true} or {"on": false}')
            set_power(self.root, parts[2], on)
        except LookupError as err:
            return self.reply(404, {"error": str(err)})
        except PermissionError as err:
            return self.reply(409, {"error": str(err)})
        except ValueError as err:
            return self.reply(400, {"error": str(err)})
        except OSError as err:                    # two clicks at once: the second finds the file already gone
            return self.reply(500, {"error": f"{type(err).__name__}: {err}"})
        self.send_data()                        # the switch has moved: answer with the files as they now are

    def log_message(self, *args) -> None:
        pass


def server(root: Path, port: int) -> ThreadingHTTPServer:
    handler = partial(type("RootedHandler", (Handler,), {"root": root}), directory=str(STATIC))
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--dump", action="store_true")
    args = parser.parse_args(argv)
    if not (args.root / "factories").is_dir():
        parser.error(f"{args.root} has no factories/ folder")
    if args.dump:
        print(json.dumps(data.build(args.root), indent=1))
        return 0
    httpd = server(args.root, args.port)
    print(f"Keiretsu: http://127.0.0.1:{httpd.server_address[1]}  (reading {args.root})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
