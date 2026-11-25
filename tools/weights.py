"""Check a supertonic-3 model folder against weights/supertonic-3.sha256 - read-only.

    python3 tools/weights.py verify <folder>

Every listed file must exist with its size and sha256; extra files are ignored. Exit 0 when all
match, 1 on any mismatch or missing file (each one named on stderr), 2 on bad usage. The model
files live in the evido artefact store, never in this repository.
"""

import hashlib
import sys
from pathlib import Path

LOCK = Path(__file__).resolve().parent.parent / "weights" / "supertonic-3.sha256"
CHUNK = 1 << 20


def read_lock(path: Path = LOCK) -> list[tuple[str, int, str]]:
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        parts = line.split("  ")
        if len(parts) != 3:
            raise ValueError(f"{path}:{number}: expected '<sha256>  <size>  <path>'")
        digest, size, name = parts
        entries.append((digest, int(size), name))
    return entries


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def verify(folder: Path, lock: Path = LOCK) -> int:
    problems = []
    total = 0
    entries = read_lock(lock)
    for digest, size, name in entries:
        path = folder / name
        if not path.is_file():
            problems.append(f"missing: {name}")
        elif path.stat().st_size != size:
            problems.append(f"size {path.stat().st_size} != {size}: {name}")
        elif _sha256(path) != digest:
            problems.append(f"sha256 mismatch: {name}")
        else:
            total += size
    for problem in problems:
        print(f"[weights] {problem}", file=sys.stderr)
    if problems:
        print(f"[weights] {len(problems)} of {len(entries)} files do not match in {folder}", file=sys.stderr)
        return 1
    print(f"[weights] {len(entries)} of {len(entries)} files match, {total} bytes: {folder}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "verify":
        print(__doc__.strip(), file=sys.stderr)
        return 2
    folder = Path(argv[1])
    if not folder.is_dir():
        print(f"[weights] not a folder: {folder}", file=sys.stderr)
        return 2
    return verify(folder)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
