"""weights/: the checksum list of the supertonic-3 snapshot and the copy of its licence."""

import hashlib
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import weights  # noqa: E402

LICENSE_SHA256 = "0d944a9110fed9a9602d60e0423a272903e7bd21ab060490774efc77c2275e9f"
RUNTIME_FILES = 16


def test_lock_is_well_formed_and_complete():
    entries = weights.read_lock()
    assert len(entries) == 26
    assert sum(size for _, size, _ in entries) == 403_513_201
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest, _, _ in entries)
    names = [name for _, _, name in entries]
    assert names == sorted(names) and len(set(names)) == len(names)
    runtime = [n for n in names if n.startswith(("onnx/", "voice_styles/"))]
    assert len(runtime) == RUNTIME_FILES


def test_licence_copy_is_the_model_licence():
    copy = ROOT / "weights" / "LICENSE-OpenRAIL-M.txt"
    assert hashlib.sha256(copy.read_bytes()).hexdigest() == LICENSE_SHA256
    licence_entry = [d for d, _, name in weights.read_lock() if name == "LICENSE"]
    assert licence_entry == [LICENSE_SHA256]


def test_verify_names_the_changed_file(tmp_path, capsys):
    small = [e for e in weights.read_lock() if e[2] in ("voice_styles/M1.json", "voice_styles/F1.json")]
    lock = tmp_path / "lock.sha256"
    lock.write_text("".join(f"{d}  {s}  {n}\n" for d, s, n in small), encoding="utf-8")
    folder = tmp_path / "model" / "voice_styles"
    folder.mkdir(parents=True)
    (folder / "M1.json").write_text("{}", encoding="utf-8")
    assert weights.verify(tmp_path / "model", lock) == 1
    err = capsys.readouterr().err
    assert "size" in err and "voice_styles/M1.json" in err
    assert "missing: voice_styles/F1.json" in err


@pytest.mark.parametrize("argv", [[], ["mirror", "x"], ["verify"]])
def test_only_verify_exists(argv):
    assert weights.main(argv) == 2
