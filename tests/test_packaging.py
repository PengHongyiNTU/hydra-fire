from __future__ import annotations

import os
import shutil
import subprocess


def test_package_build_smoke(tmp_path):
    uv = shutil.which("uv")
    if uv is None:
        raise AssertionError("uv is required for the packaging smoke test")

    env = {**os.environ, "UV_CACHE_DIR": str(tmp_path / "uv-cache")}
    subprocess.run(
        [uv, "build", "--out-dir", str(tmp_path)],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )

    artifacts = {path.suffix for path in tmp_path.iterdir()}
    assert ".whl" in artifacts
    assert ".gz" in artifacts
