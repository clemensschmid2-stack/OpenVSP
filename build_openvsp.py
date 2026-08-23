#!/usr/bin/env python3
"""Configure and build the complete OpenVSP distribution on Windows."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
DEFAULT_BUILD_DIR = ROOT / "build-msvc-full"


def run(command: list[str]) -> None:
    print("\n>", subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def find_python_library(python: Path) -> Path:
    version = subprocess.check_output(
        [str(python), "-c", "import sys; print(f'python{sys.version_info.major}{sys.version_info.minor}.lib')"],
        text=True,
    ).strip()
    candidates = [python.parent / "libs" / version]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        f"Could not find {version}. Use a Python installation that includes development files."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build OpenVSP, its GUI, VSPAERO, tools, documentation, and Python API."
    )
    parser.add_argument("--clean", action="store_true", help="delete the build directory first")
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    parser.add_argument("--config", choices=("Release", "Debug"), default="Release")
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(4, max(1, os.cpu_count() or 1)),
        help="parallel build jobs (default: up to 4; use 1 or 2 to reduce RAM use)",
    )
    parser.add_argument(
        "--python",
        type=Path,
        default=Path(sys.executable),
        help="Python executable used for the API wrapper (default: this interpreter)",
    )
    args = parser.parse_args()

    if os.name != "nt":
        parser.error("This launcher targets Windows and Visual Studio 2022.")
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")

    cmake = shutil.which("cmake")
    if not cmake:
        parser.error("cmake was not found on PATH")

    python = args.python.expanduser().resolve()
    if not python.is_file():
        parser.error(f"Python executable does not exist: {python}")
    swig = shutil.which("swig")
    if not swig:
        bundled_swig = python.parent / "Library" / "bin" / "swig.exe"
        swig = str(bundled_swig) if bundled_swig.is_file() else None
    if not swig:
        parser.error("swig was not found on PATH or in the selected Python environment")
    python_include = python.parent / "include"
    if not python_include.is_dir():
        parser.error(f"Python include directory does not exist: {python_include}")
    try:
        python_library = find_python_library(python)
    except FileNotFoundError as error:
        parser.error(str(error))

    build_dir = args.build_dir.expanduser().resolve()
    if args.clean and build_dir.exists():
        if build_dir == ROOT or ROOT not in build_dir.parents:
            parser.error(f"refusing to clean a directory outside the OpenVSP tree: {build_dir}")
        print(f"Removing {build_dir}")
        shutil.rmtree(build_dir)

    configure = [
        cmake,
        "-S", str(ROOT / "SuperProject"),
        "-B", str(build_dir),
        "-G", "Visual Studio 17 2022",
        "-A", "x64",
        f"-DCMAKE_INSTALL_PREFIX={build_dir / 'install'}",
        "-DVSP_NO_GRAPHICS=OFF",
        "-DVSP_NO_VSPAERO=OFF",
        "-DVSP_NO_API_WRAPPERS=OFF",
        "-DVSP_NO_HELP=OFF",
        "-DVSP_NO_DOC=OFF",
        "-DVSP_NO_PYDOC=OFF",
        f"-DPYTHON_EXECUTABLE={python}",
        f"-DPYTHON_LIBRARY={python_library}",
        f"-DPYTHON_INCLUDE_DIR={python_include}",
        f"-DPYTHON_INCLUDE_PATH={python_include}",
        f"-DSWIG_EXECUTABLE={Path(swig).resolve()}",
    ]
    run(configure)
    run([
        cmake,
        "--build", str(build_dir),
        "--config", args.config,
        "--parallel", str(args.jobs),
    ])

    install_dir = build_dir / "install"
    expected = ["vsp.exe", "vspaero.exe", "vspscript.exe", "vspviewer.exe"]
    missing = [name for name in expected if not (install_dir / name).is_file()]
    if missing:
        print(f"\nBuild finished, but expected outputs are missing: {', '.join(missing)}", file=sys.stderr)
        return 1

    print(f"\nFull OpenVSP build completed successfully.\nExecutables: {install_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(f"\nBuild failed with exit code {error.returncode}.", file=sys.stderr)
        raise SystemExit(error.returncode)
