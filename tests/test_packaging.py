"""pyproject.toml of this build: no network-client dependency, a version distinct from PyPI."""

import re
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
NETWORK_CLIENTS = ("huggingface-hub", "huggingface_hub", "httpx", "httpx2", "requests", "aiohttp")


def _project() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]


def _names(requirements) -> set[str]:
    return {re.split(r"[\s<>=!~;\[]", req, maxsplit=1)[0].lower() for req in requirements}


def test_runtime_and_serve_dependencies_carry_no_network_client():
    project = _project()
    runtime = _names(project["dependencies"]) | _names(project["optional-dependencies"]["serve"])
    assert not runtime & set(NETWORK_CLIENTS), sorted(runtime)


def test_version_is_the_evido_build_of_upstream_1_3_1():
    assert re.fullmatch(r"1\.3\.1\+evido\.[1-9][0-9]*", _project()["version"])


def test_package_reports_the_pyproject_version():
    import supertonic

    assert supertonic.__version__ == _project()["version"]
