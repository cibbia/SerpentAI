from __future__ import annotations

import json, os, hashlib, shutil
from pathlib import Path
from typing import List, Dict

import requests  # type: ignore
from tqdm import tqdm  # type: ignore

_REGISTRY_URL = "https://raw.githubusercontent.com/SerpentAI/ModelHub/main/registry.json"
_CACHE_DIR = Path.home() / ".serpent" / "models"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _download_registry() -> List[Dict]:
    try:
        r = requests.get(_REGISTRY_URL, timeout=5)
        if r.ok:
            return r.json()
    except Exception:
        pass
    # fallback minimal sample
    return [
        {
            "id": "flappy-ppo",
            "game": "Generic_QUICKSTART",
            "algo": "ppo",
            "format": "onnx",
            "url": "https://huggingface.co/serpent/flappy/resolve/main/flappy.onnx",
            "sha256": "dummy",
            "size": 123456,
        }
    ]


def list_models() -> List[Dict]:
    return _download_registry()


def local_models() -> List[Path]:
    return list(_CACHE_DIR.glob("**/*.onnx")) + list(_CACHE_DIR.glob("**/*.zip"))


def download_model(model_id: str) -> Path:
    registry = {m["id"]: m for m in _download_registry()}
    if model_id not in registry:
        raise ValueError("Unknown model id")
    meta = registry[model_id]
    dest_dir = _CACHE_DIR / meta["game"] / model_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(meta["url"]).name
    dest = dest_dir / filename
    if dest.exists():
        return dest
    r = requests.get(meta["url"], stream=True)
    total = int(r.headers.get("Content-Length", 0))
    with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=filename) as pbar:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
    # Verify checksum if provided
    if meta.get("sha256") and meta["sha256"] != "dummy":
        h = hashlib.sha256()
        with open(dest, "rb") as f:
            for b in iter(lambda: f.read(8192), b""):
                h.update(b)
        if h.hexdigest() != meta["sha256"]:
            dest.unlink(missing_ok=True)
            raise ValueError("SHA256 mismatch after download. File removed.")
    return dest