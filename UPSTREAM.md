# Upstream

This repository carries the Python package `supertonic` as maintained for evido. It descends from
the upstream release 1.3.1, which is final: upstream archived its repositories on 2026-09-09 and
announced that development, support and security patches have ended.

| Item | Value |
|---|---|
| Repository | https://github.com/supertone-oss-archive/supertonic-py (formerly `supertone-inc/supertonic-py`, archived) |
| Tag | `v1.3.1` |
| Commit | `908a56486e821e833a80530ff0cae3ad0b046fce` |
| PyPI sdist | `supertonic-1.3.1.tar.gz`, sha256 `4367e8f61afea618dac948f6bee55fed4721ad66ca2d3fc90771a2a66740731e` |
| Licence | MIT, Copyright (c) 2025 Supertone Inc. (`LICENSE`) |
| Checksums of the import | `upstream/supertonic-1.3.1.sha256` - one line per imported file |

Not imported from the tag: `docs/`, `assets/`, `notebook/`, `mkdocs.yml`, `llms.txt` (documentation
site and media), `examples/` (they load the model from Hugging Face), `.github/workflows/`
(unpinned actions, one publishes to PyPI), `CHANGELOG.md`, `SECURITY.md`,
`.pre-commit-config.yaml`, `requirements*.txt`, `.gitignore`.

## Files that differ from 1.3.1

Every imported file not listed here is byte-identical to the import (`tests/test_upstream_parity.py`
enforces both directions).

