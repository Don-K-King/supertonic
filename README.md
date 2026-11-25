# supertonic (evido build)

The Python text-to-speech package `supertonic` 1.3.1 by Supertone Inc., maintained for evido after
upstream archived it. The evido image `evido-kaposg-supertonic-cpu` installs the wheel built here.

| What | Where |
|---|---|
| Provenance, deviations from 1.3.1 | `UPSTREAM.md` |
| Who owns what, model licence | `NOTICE.md`, `LICENSE`, `weights/LICENSE-OpenRAIL-M.txt` |
| Model checksums (supertonic-3, 26 files) | `weights/supertonic-3.sha256` - the files live in the evido artefact store |

This build has no network path: `download_model` and `supertonic download` refuse, `huggingface-hub`
is no dependency, and the server has no `/docs` or `/redoc` page. A missing model is an error.
Version: `1.3.1+evido.N`.

## Tests

```sh
tools/check.sh
```

Builds `.venv` offline from the evido artefact store (`EVIDO_ARTIFACT_STORE`, default
`../evido-v1.0/artifact-store`) and runs every test against the working tree, with the model from
`SUPERTONIC_TEST_MODEL` (default: the store's supertonic-3 folder). Without a model the model tests
are skipped with a reason.

## Wheel

```sh
tools/build-wheel.sh --commit <sha> --build-wheels <wheel folder> --build-lock <hash lock> --out <dir>
```

Offline (`--no-index`), from `git archive <sha>`, build tools at the versions and hashes of the
build lock; two builds of one commit give the same sha256.

## Weights

```sh
python3 tools/weights.py verify <model folder>
```

Checks every file of `weights/supertonic-3.sha256` (size, sha256) in a folder; read-only.
