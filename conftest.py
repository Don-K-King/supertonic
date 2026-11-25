"""Session setup for every test: the model comes from the evido artefact store, never a download.

SUPERTONIC_TEST_MODEL names the model snapshot (default: the store folder of the sibling
evido-v1.0 checkout). The session builds its own model directory of symlinks to the snapshot's
files and points SUPERTONIC_CACHE_DIR / SUPERTONIC_CUSTOM_STYLES_DIR at it, so a test that
creates files writes there and never into the store. Without a snapshot the package's download
path is replaced by a refusal, and every test that fails on that refusal is reported as skipped
with the reason - never as passed.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

MODEL_ENV = "SUPERTONIC_TEST_MODEL"
DEFAULT_MODEL = (
    Path(__file__).resolve().parent.parent
    / "evido-v1.0"
    / "artifact-store"
    / "supertonic"
    / "supertone-supertonic-3-724fb5abbf55"
)
LINKED_DIRS = ("onnx", "voice_styles")
REQUIRED = (
    "onnx/duration_predictor.onnx",
    "onnx/text_encoder.onnx",
    "onnx/vector_estimator.onnx",
    "onnx/vocoder.onnx",
    "onnx/tts.json",
    "onnx/unicode_indexer.json",
)
SKIP_REASON = f"model snapshot not available - set {MODEL_ENV} to the supertonic-3 store folder"

_session_dir = None


class ModelUnavailable(RuntimeError):
    """The test session has no model snapshot; nothing is ever downloaded."""


def model_source() -> Path:
    return Path(os.environ.get(MODEL_ENV) or DEFAULT_MODEL)


def model_available() -> bool:
    source = model_source()
    return all((source / name).is_file() for name in REQUIRED)


def _refuse_download(*_args, **_kwargs):
    raise ModelUnavailable(SKIP_REASON)


def pytest_configure(config):
    global _session_dir
    _session_dir = Path(tempfile.mkdtemp(prefix="supertonic-test-model-"))
    source = model_source()
    if model_available():
        for sub in LINKED_DIRS:
            (_session_dir / sub).mkdir()
            for item in sorted((source / sub).iterdir()):
                (_session_dir / sub / item.name).symlink_to(item.resolve())
    else:
        import supertonic.loader

        supertonic.loader.download_model = _refuse_download
    os.environ["SUPERTONIC_CACHE_DIR"] = str(_session_dir)
    os.environ["SUPERTONIC_CUSTOM_STYLES_DIR"] = str(_session_dir / "custom_styles")


def pytest_report_header(config):
    state = "present" if model_available() else "MISSING (model tests skip)"
    return f"supertonic test model: {model_source()} - {state}"


def _caused_by_missing_model(exc) -> bool:
    # The CLI catches the refusal and exits 1, so the refusal can sit in the chain of a
    # SystemExit rather than be the raised exception itself.
    seen = set()
    while exc is not None and id(exc) not in seen:
        if isinstance(exc, ModelUnavailable):
            return True
        seen.add(id(exc))
        exc = exc.__cause__ or exc.__context__
    return False


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if call.excinfo is not None and _caused_by_missing_model(call.excinfo.value):
        report.outcome = "skipped"
        report.longrepr = (str(item.path), item.location[1], f"Skipped: {SKIP_REASON}")


def pytest_unconfigure(config):
    # rmtree unlinks the symlinks; it never follows them into the store.
    if _session_dir is not None:
        shutil.rmtree(_session_dir, ignore_errors=True)
