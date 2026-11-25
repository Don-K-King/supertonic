"""A built wheel (SUPERTONIC_WHEEL=<path>) carries the package, its licence and no download path.

Skipped without SUPERTONIC_WHEEL. With SUPERTONIC_BUILD_LOCK=<file> the wheel's Generator line
must name the setuptools version of that build lock - the version is written into the wheel, so
another setuptools means other bytes.
"""

import os
import re
import tomllib
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WHEEL = os.environ.get("SUPERTONIC_WHEEL")
BUILD_LOCK = os.environ.get("SUPERTONIC_BUILD_LOCK")

pytestmark = pytest.mark.skipif(not WHEEL, reason="set SUPERTONIC_WHEEL to a built wheel")


def _version() -> str:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


def _wheel() -> zipfile.ZipFile:
    return zipfile.ZipFile(WHEEL)


def _dist_info() -> str:
    return f"supertonic-{_version()}.dist-info"


def test_wheel_holds_exactly_the_package_files():
    names = set(_wheel().namelist())
    package = {n for n in names if n.startswith("supertonic/")}
    expected = {p.relative_to(ROOT).as_posix() for p in (ROOT / "supertonic").rglob("*.py")}
    assert package == expected
    assert len(package) == 13
    assert f"{_dist_info()}/licenses/LICENSE" in names


def test_wheel_metadata_names_this_build_without_huggingface():
    metadata = _wheel().read(f"{_dist_info()}/METADATA").decode("utf-8")
    assert re.search(rf"^Version: {re.escape(_version())}$", metadata, flags=re.MULTILINE)
    requires = [line for line in metadata.splitlines() if line.startswith("Requires-Dist:")]
    assert requires
    assert not [line for line in requires if "huggingface" in line.lower()], requires


def test_wheel_generator_is_the_locked_setuptools():
    if not BUILD_LOCK:
        pytest.skip("set SUPERTONIC_BUILD_LOCK to the build lock the wheel was built with")
    locked = re.search(r"^setuptools==(\S+)", Path(BUILD_LOCK).read_text(encoding="utf-8"), re.M)
    assert locked, f"{BUILD_LOCK} pins no setuptools"
    generator = _wheel().read(f"{_dist_info()}/WHEEL").decode("utf-8")
    assert f"Generator: setuptools ({locked.group(1)})" in generator, generator
