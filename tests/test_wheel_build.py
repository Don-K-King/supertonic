"""tools/build-wheel.sh: the wheel's bytes follow its inputs, never the time of the commit built.

d887bd1 and 0e0c9e1 hold the same tree (0e0c9e1 is an empty correction commit) at different commit
times. With SOURCE_DATE_EPOCH taken from the built commit itself they gave 1.3.1+evido.1 two
different sha256, so a re-lock from HEAD could not re-pin the stored wheel. Needs uv, python3.12
and the build tools of the evido build lock: the store folder supertonic-wheels-cp312
(EVIDO_ARTIFACT_STORE, default ../evido-v1.0/artifact-store) and SUPERTONIC_BUILD_LOCK (default
../evido-v1.0/docker/supertonic/requirements-build.txt); skipped without them.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
EVIDO = ROOT.parent / "evido-v1.0"
STORE = Path(os.environ.get("EVIDO_ARTIFACT_STORE") or EVIDO / "artifact-store")
BUILD_WHEELS = STORE / "python" / "supertonic-wheels-cp312"
BUILD_LOCK = Path(
    os.environ.get("SUPERTONIC_BUILD_LOCK") or EVIDO / "docker" / "supertonic" / "requirements-build.txt"
)
SAME_TREE = (
    "d887bd1bd59720c0b8b3a692f2efa90297f1b1c2",
    "0e0c9e1fae9f18efd463f8aa98be6b2356ee465f",
)


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)


def _missing() -> str | None:
    if shutil.which("uv") is None:
        return "uv not on PATH"
    if not BUILD_WHEELS.is_dir():
        return f"build tools folder missing: {BUILD_WHEELS} (set EVIDO_ARTIFACT_STORE)"
    if not BUILD_LOCK.is_file():
        return f"build lock missing: {BUILD_LOCK} (set SUPERTONIC_BUILD_LOCK)"
    for commit in SAME_TREE:
        if _git("cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            return f"commit {commit} not in this clone"
    return None


def _build(commit: str, out: Path) -> Path:
    result = subprocess.run(
        [
            "bash", str(ROOT / "tools" / "build-wheel.sh"), "--commit", commit,
            "--build-wheels", str(BUILD_WHEELS), "--build-lock", str(BUILD_LOCK), "--out", str(out),
        ],
        capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, result.stderr
    wheel = Path(result.stdout.split()[0])
    assert wheel.parent == out and wheel.is_file(), result.stdout
    return wheel


def test_two_commits_with_the_same_tree_give_the_same_wheel(tmp_path):
    reason = _missing()
    if reason:
        pytest.skip(reason)
    first, second = SAME_TREE
    assert _git("diff", "--quiet", first, second).returncode == 0, "the case needs two equal trees"
    times = {_git("show", "-s", "--format=%ct", commit).stdout.strip() for commit in SAME_TREE}
    assert len(times) == 2, "the case needs two different commit times"

    wheels = [_build(commit, tmp_path / commit[:7]) for commit in SAME_TREE]
    assert wheels[0].name == wheels[1].name
    digests = [hashlib.sha256(wheel.read_bytes()).hexdigest() for wheel in wheels]
    assert digests[0] == digests[1], dict(zip(SAME_TREE, digests))
