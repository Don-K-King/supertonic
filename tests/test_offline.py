"""This build of supertonic has no network path: no client import, no download, no CDN pages.

The socket guard refuses every connection except loopback and every name resolution, so a
load or a synthesis that reached for the network fails here instead of on an air-gapped host.
"""

import ast
import os
import socket
from pathlib import Path

import numpy as np
import pytest

PACKAGE = Path(__file__).resolve().parent.parent / "supertonic"
FORBIDDEN_MODULES = ("huggingface_hub", "httpx", "httpx2", "requests", "aiohttp", "urllib3")
FORBIDDEN_NAMES = ("snapshot_download", "hf_hub_download")
LOOPBACK = ("127.0.0.1", "::1", "localhost")


def _imports(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            yield node.module
            for alias in node.names:
                yield f"{node.module}.{alias.name}"


def _forbidden(module: str) -> bool:
    root = module.split(".", 1)[0]
    return root in FORBIDDEN_MODULES or module == "urllib.request"


def test_package_imports_no_network_client():
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        found += [f"{path.name}: import {m}" for m in _imports(tree) if _forbidden(m)]
        found += [
            f"{path.name}: {node.id if isinstance(node, ast.Name) else node.attr}"
            for node in ast.walk(tree)
            if (isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES)
            or (isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_NAMES)
        ]
    assert not found, found


def test_download_model_refuses(tmp_path):
    from supertonic.loader import DownloadDisabledError, download_model

    with pytest.raises(DownloadDisabledError, match="never downloads"):
        download_model(tmp_path / "model", "supertonic-3")
    assert not (tmp_path / "model").exists()


def test_missing_model_raises_instead_of_downloading(tmp_path):
    from supertonic.loader import DownloadDisabledError, load_model

    with pytest.raises(DownloadDisabledError):
        load_model(tmp_path, auto_download=True, model_name="supertonic-3")
    with pytest.raises(FileNotFoundError, match="never downloads"):
        load_model(tmp_path, auto_download=False, model_name="supertonic-3")


@pytest.fixture
def no_network(monkeypatch):
    real_connect = socket.socket.connect

    def guarded_connect(self, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if host not in LOOPBACK:
            raise AssertionError(f"network connection attempted: {address!r}")
        return real_connect(self, address, *args, **kwargs)

    def refuse_resolution(*args, **kwargs):
        raise AssertionError(f"name resolution attempted: {args!r}")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket, "getaddrinfo", refuse_resolution)
    monkeypatch.setattr(socket, "gethostbyname", refuse_resolution)


def test_load_and_synthesis_without_network(no_network):
    model_dir = Path(os.environ["SUPERTONIC_CACHE_DIR"])
    if not (model_dir / "onnx" / "vocoder.onnx").exists():
        pytest.skip("model snapshot not available - set SUPERTONIC_TEST_MODEL")
    from supertonic import TTS

    tts = TTS(model="supertonic-3", auto_download=False)
    assert len(tts.voice_style_names) == 10
    wav, duration = tts.synthesize(
        "Guten Tag. Bitte nennen Sie Ihren Namen.",
        voice_style=tts.get_voice_style(voice_name="M1"),
        lang="de",
    )
    assert np.asarray(wav).size > 0
    assert float(np.asarray(duration).reshape(-1)[0]) > 0.5


def test_cli_download_refuses_and_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        _run_cli(["download"])
    assert exc_info.value.code == 1
    assert "never downloads" in capsys.readouterr().err


def test_cli_serve_does_not_advertise_docs(monkeypatch, capsys):
    pytest.importorskip("fastapi")
    import uvicorn

    from supertonic.cli import cmd_serve, create_parser

    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: None)
    monkeypatch.setattr("supertonic.server.create_app", lambda **kwargs: object())
    cmd_serve(create_parser().parse_args(["serve"]))
    out = capsys.readouterr().out
    assert "listening on" in out
    assert "/docs" not in out


def _run_cli(argv):
    import sys

    from supertonic.cli import main

    saved = sys.argv
    sys.argv = ["supertonic", *argv]
    try:
        main()
    finally:
        sys.argv = saved


def test_app_has_no_cdn_documentation_pages():
    pytest.importorskip("fastapi")
    from supertonic.server import create_app

    app = create_app(model="supertonic-3")
    paths = {getattr(route, "path", None) for route in app.router.routes}
    assert not paths & {"/docs", "/docs/oauth2-redirect", "/redoc"}, paths
    schema_paths = app.openapi()["paths"]
    assert "/v1/audio/speech" in schema_paths
    assert "/v1/health" in schema_paths
