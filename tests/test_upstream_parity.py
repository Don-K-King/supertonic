"""Every imported upstream file is either byte-identical to 1.3.1 or named in UPSTREAM.md.

The checksum list upstream/supertonic-1.3.1.sha256 was written from the import commit;
UPSTREAM.md, section "Files that differ from 1.3.1", is the closed list of our deviations.
"""

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKSUMS = ROOT / "upstream" / "supertonic-1.3.1.sha256"
UPSTREAM_MD = ROOT / "UPSTREAM.md"
DEVIATION_HEADING = "## Files that differ from 1.3.1"


def _checksums() -> dict[str, str]:
    entries = {}
    for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        assert re.fullmatch(r"[0-9a-f]{64}", digest), line
        entries[path] = digest
    return entries


def _deviations() -> list[str]:
    text = UPSTREAM_MD.read_text(encoding="utf-8")
    _, found, section = text.partition(DEVIATION_HEADING)
    assert found, f"UPSTREAM.md lacks the heading {DEVIATION_HEADING!r}"
    section = section.split("\n## ", 1)[0]
    return re.findall(r"^- `([^`]+)`", section, flags=re.MULTILINE)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_checksum_list_covers_the_import():
    entries = _checksums()
    assert len(entries) == 29
    assert sum(1 for p in entries if p.startswith("supertonic/")) == 13


def test_deviation_list_names_only_imported_files():
    deviations = _deviations()
    assert len(deviations) == len(set(deviations)), deviations
    unknown = sorted(set(deviations) - set(_checksums()))
    assert not unknown, f"UPSTREAM.md lists files that were never imported: {unknown}"


def test_every_file_outside_the_deviation_list_is_unchanged():
    deviations = set(_deviations())
    changed = sorted(
        path
        for path, digest in _checksums().items()
        if path not in deviations and _sha256(ROOT / path) != digest
    )
    assert not changed, f"changed against 1.3.1 but not listed in UPSTREAM.md: {changed}"


def test_every_listed_deviation_really_differs():
    entries = _checksums()
    identical = sorted(
        path
        for path in _deviations()
        if (ROOT / path).is_file() and _sha256(ROOT / path) == entries[path]
    )
    assert not identical, f"UPSTREAM.md lists files identical to 1.3.1: {identical}"
