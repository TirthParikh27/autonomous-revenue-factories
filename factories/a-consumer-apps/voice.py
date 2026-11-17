#!/usr/bin/env python3
"""Speak one line of ad narration to an audio file and print how long it is.

    python3 voice.py --file demand/<id>/ads/ad-1/audio/vo-1.txt -o demand/<id>/ads/ad-1/audio/vo-1

Uses the operator's HeyGen voice when a HeyGen login or key is available, because it sounds human.
Otherwise it falls back to the free local voice (`npx hyperframes tts`) and says so. The output path
is given without an extension: HeyGen writes .mp3, the local voice writes .wav. Prints one JSON line:
{"provider", "output", "durationSeconds", "note"}.

Credentials, first found wins: HEYGEN_API_KEY, then ~/.heygen/credentials as written by
`heygen auth login`. This script never refreshes or rewrites a login; if it has expired it says how
to renew it and uses the local voice. Nothing secret is printed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

HEYGEN_SPEECH_URL = "https://api.heygen.com/v3/voices/speech"
DEFAULT_HEYGEN_VOICE = "05f19352e8f74b0392a8f411eba40de1"   # "Marcia", HeyGen's public default English voice
HYPERFRAMES = "hyperframes@0.9.59"


def heygen_headers(env=os.environ, home: Optional[Path] = None) -> Tuple[Optional[dict], str]:
    """Return (auth headers, note). Headers are None when no usable credential exists."""
    if env.get("HEYGEN_API_KEY"):
        return {"X-Api-Key": env["HEYGEN_API_KEY"]}, "HeyGen API key from the environment"
    cred_file = Path(env.get("HEYGEN_CONFIG_DIR") or (home or Path.home()) / ".heygen") / "credentials"
    if not cred_file.exists():
        return None, "no HeyGen login found"
    raw = cred_file.read_text().strip()
    if not raw.startswith("{"):
        return {"X-Api-Key": raw}, "HeyGen API key from the credentials file"
    try:
        cred = json.loads(raw)
    except ValueError:
        return None, "HeyGen credentials file is unreadable"
    oauth = cred.get("oauth") or {}
    if oauth.get("access_token"):
        expires = oauth.get("expires_at")
        expired = False
        if expires:
            try:
                when = dt.datetime.fromisoformat(expires.replace("Z", "+00:00"))
                expired = when - dt.timedelta(minutes=1) < dt.datetime.now(dt.timezone.utc)
            except ValueError:
                expired = True
        if not expired:
            return {"Authorization": "Bearer " + oauth["access_token"], "X-HeyGen-Source": "cli"}, "HeyGen login"
        if not cred.get("api_key"):
            return None, "HeyGen login has expired; the operator renews it with `heygen auth status` or `heygen auth login --oauth`"
    if cred.get("api_key"):
        return {"X-Api-Key": cred["api_key"]}, "HeyGen API key from the credentials file"
    return None, "no HeyGen login found"


def speak_heygen(text: str, out: Path, voice: str, headers: dict, opener=urllib.request.urlopen) -> dict:
    body = json.dumps({"text": text, "voice_id": voice, "speed": 1}).encode()
    req = urllib.request.Request(HEYGEN_SPEECH_URL, data=body, method="POST",
                                 headers={**headers, "Content-Type": "application/json", "X-HeyGen-Client-Source": "factory"})
    with opener(req, timeout=120) as resp:
        payload = json.loads(resp.read())
    data = payload.get("data") or payload
    url = data.get("audio_url") or ""
    if not url.startswith("https://"):
        raise RuntimeError("HeyGen returned no audio")
    with opener(urllib.request.Request(url), timeout=120) as resp:
        audio = resp.read()
    target = out.with_name(out.name + ".mp3")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(audio)
    ends = [w.get("end") for w in data.get("word_timestamps") or [] if isinstance(w.get("end"), (int, float))]
    duration = data.get("duration") or (max(ends) + 0.15 if ends else None)
    return {"provider": "heygen", "output": str(target), "durationSeconds": round(float(duration), 3) if duration else None}


def speak_local(text: str, out: Path, voice: Optional[str], run=subprocess.run) -> dict:
    target = out.with_name(out.name + ".wav")
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["npx", "-y", HYPERFRAMES, "tts", text, "-o", str(target), "--json"]
    if voice:
        cmd += ["-v", voice]
    proc = run(cmd, capture_output=True, text=True, timeout=300)
    result = None
    for line in reversed(proc.stdout.splitlines()):
        if line.strip().startswith("{"):
            try:
                result = json.loads(line)
                break
            except ValueError:
                continue
    if proc.returncode != 0 or not result or not result.get("ok"):
        raise RuntimeError("local voice failed: " + (proc.stderr or proc.stdout).strip()[-300:])
    return {"provider": "local", "output": str(target), "durationSeconds": result.get("durationSeconds")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("text", nargs="?")
    parser.add_argument("--file", type=Path, help="read the line from a text file (safest for quotes and $ signs)")
    parser.add_argument("-o", "--output", required=True, type=Path, help="output path without an extension")
    parser.add_argument("--voice", help="voice id for the provider in use")
    parser.add_argument("--provider", choices=["auto", "heygen", "local"], default="auto")
    args = parser.parse_args(argv)
    if args.file:
        args.text = args.file.read_text().strip()
    if not args.text:
        parser.error("give the line as an argument or with --file")

    notes = []
    if args.provider in ("auto", "heygen"):
        headers, note = heygen_headers()
        notes.append(note)
        if headers:
            try:
                result = speak_heygen(args.text, args.output, args.voice or DEFAULT_HEYGEN_VOICE, headers)
                print(json.dumps({**result, "note": note}))
                return 0
            except Exception as exc:  # fall back, but say why
                notes.append("HeyGen call failed: " + str(exc)[:200])
        if args.provider == "heygen":
            print(json.dumps({"provider": None, "note": "; ".join(notes)}))
            return 1
    try:
        result = speak_local(args.text, args.output, args.voice if args.provider == "local" else None)
    except Exception as exc:
        print(json.dumps({"provider": None, "note": "; ".join(notes + [str(exc)[:300]])}))
        return 1
    print(json.dumps({**result, "note": "; ".join(notes + ["used the free local voice"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
