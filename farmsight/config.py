from __future__ import annotations
from pathlib import Path
import yaml

def load_config(path: str | None = None) -> dict:
    p = Path(path) if path else Path(__file__).resolve().parents[1] / "config.yaml"
    with open(p, "r") as f:
        return yaml.safe_load(f)
