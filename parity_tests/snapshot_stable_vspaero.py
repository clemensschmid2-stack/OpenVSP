#!/usr/bin/env python3
"""Snapshot a custom VSPAERO binary for optional historical regression.

The snapshot is not an official parity reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent / "build-msvc-full" / "install" / "vspaero.exe"
DEFAULT_DESTINATION = HERE / "baselines" / "stable-main" / "vspaero.exe"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_file():
        parser.error(f"VSPAERO executable not found: {source}")
    if destination.exists() and not args.force:
        parser.error(f"Snapshot already exists: {destination}; use --force to replace it")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    try:
        revision = subprocess.check_output(
            ["git", "-C", str(HERE.parent), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "unknown"
    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
        "git_revision": revision,
        "sha256": digest,
        "size": destination.stat().st_size,
    }
    destination.with_suffix(".json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Stable VSPAERO snapshot: {destination}")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
