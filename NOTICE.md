# Notice

| Part | Owner | Licence |
|---|---|---|
| The package `supertonic/`, its tests, `pyproject.toml`, `README.md` as imported | Supertone Inc. | MIT (`LICENSE`) |
| Our changes to those files, and every file this repository adds | the evido maintainers | MIT, same terms as `LICENSE` |
| Model `Supertone/supertonic-3` and its ten voice styles `M1`-`M5`, `F1`-`F5` | Supertone Inc. | BigScience OpenRAIL-M of 2022-08-18 (`weights/LICENSE-OpenRAIL-M.txt`) |

The model and the voice styles are NOT part of this repository. Only their checksum list
(`weights/supertonic-3.sha256`) and a copy of their licence are kept here; the files themselves live
in the artefact store of the evido build.

Anyone who uses or passes on the model must observe the use restrictions of Attachment A of its
licence and pass them on (paragraph 4a and 5 of that licence).

## The model version we use

| Item | Value |
|---|---|
| Model repository | https://huggingface.co/Supertone/supertonic-3 |
| Pinned commit | `724fb5abbf5502583fb520898d45929e62f02c0b` (2026-05-06, "Initial Supertonic 3 release") |
| Head of the model repository | `3cadd1ee6394adea1bd021217a0e650ede09a323` (2026-05-18) |
| Runtime files at the head vs. the pinned commit | 16 of 16 identical (`onnx/*`, `voice_styles/*`; LFS files by sha256, the others by git blob id), checked 2026-11-25 |

Paragraph 7 of the model licence asks for reasonable efforts to use the latest version of the
model. The four commits after the pinned one change the model card and audio samples only; every
file the runtime loads is the same, so the pinned snapshot IS the latest model version.
