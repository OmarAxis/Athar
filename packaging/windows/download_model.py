"""Download the open-weights model into the `models` folder. Standard library only.

This is the one part of the package that uses the internet, and only when the person runs it. It
fetches one file from one address, can continue a download that was interrupted, and checks the
file against a known checksum before it is used.
"""
from __future__ import annotations

import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL_FILE = "Qwen3.5-9B-Q4_K_M.gguf"
MODEL_URL = "https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF/resolve/main/" + MODEL_FILE
MODEL_BYTES = 5_627_044_256
MODEL_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
CHUNK = 1024 * 1024


def sha256_of(path: Path, say=None) -> str:
    digest = hashlib.sha256()
    done = 0
    with path.open("rb") as fh:
        while block := fh.read(CHUNK * 8):
            digest.update(block)
            done += len(block)
            if say:
                say(done)
    return digest.hexdigest()


def progress(done: int, total: int, started: float, first: int) -> str:
    speed = (done - first) / max(time.monotonic() - started, 0.001)
    left = (total - done) / speed if speed > 0 else 0
    return (f"\r  {done / 1024 ** 3:5.2f} of {total / 1024 ** 3:.2f} GB  {100 * done / total:5.1f}%  "
            f"{speed / 1024 ** 2:5.1f} MB/s  about {int(left // 60)} min left   ")


def download(url: str, target: Path, total: int, out=sys.stdout) -> None:
    """Fetch `url` into `target`, continuing from a partial file if there is one."""
    part = target.with_suffix(target.suffix + ".part")
    have = part.stat().st_size if part.is_file() else 0
    if have > total:
        part.unlink()
        have = 0
    if have < total:
        request = urllib.request.Request(url, headers={"User-Agent": "athar-package"})
        if have:
            request.add_header("Range", f"bytes={have}-")
        with urllib.request.urlopen(request, timeout=60) as reply:
            if have and reply.status != 206:
                have = 0  # the server sent the whole file again
            started, first = time.monotonic(), have
            with part.open("ab" if have else "wb") as fh:
                while block := reply.read(CHUNK):
                    fh.write(block)
                    have += len(block)
                    out.write(progress(have, total, started, first))
                    out.flush()
        out.write("\n")
    part.replace(target)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    models = root / "models"
    models.mkdir(exist_ok=True)
    target = models / MODEL_FILE
    print("\n  Athar: download the model\n  -------------------------------")
    print(f"  File: {MODEL_FILE} (5.2 GB, open weights, Apache 2.0 licence)")
    print(f"  From: {MODEL_URL}\n")
    if target.is_file() and target.stat().st_size == MODEL_BYTES:
        print("  The model is already in the models folder. Nothing to do.")
        return 0
    try:
        download(MODEL_URL, target, MODEL_BYTES)
    except (urllib.error.URLError, OSError) as problem:
        print(f"\n  The download stopped: {problem}")
        print("  Run this again and it continues from where it stopped.")
        return 1
    print("  Checking the file...")
    if sha256_of(target) != MODEL_SHA256:
        target.unlink()
        print("  The file does not match its checksum, so it was removed. Please run this again.")
        return 1
    print("  Done. Start Athar again and the model will run on this computer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
