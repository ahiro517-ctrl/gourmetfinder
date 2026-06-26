"""設定ファイル(YAML)と環境変数の読み込み。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# リポジトリ直下の config/ ディレクトリ
ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class Settings:
    config: dict[str, Any]
    weights: dict[str, Any]
    chains: dict[str, Any]

    # 環境変数（GitHub Actions の Secrets から渡される）
    places_api_key: str = ""
    service_account_json: str = ""
    spreadsheet_id: str = ""

    @property
    def weight_values(self) -> dict[str, float]:
        return dict(self.weights.get("weights", {}))

    @property
    def chain_keywords(self) -> list[str]:
        return list(self.chains.get("keywords", []))


def load_settings(config_dir: Path = CONFIG_DIR) -> Settings:
    return Settings(
        config=_load_yaml(config_dir / "config.yaml"),
        weights=_load_yaml(config_dir / "weights.yaml"),
        chains=_load_yaml(config_dir / "chains.yaml"),
        places_api_key=os.environ.get("GOOGLE_PLACES_API_KEY", ""),
        service_account_json=os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", ""),
        spreadsheet_id=os.environ.get("GOURMET_SPREADSHEET_ID", ""),
    )


def save_weights(weights: dict[str, Any], config_dir: Path = CONFIG_DIR) -> None:
    """学習後の重みを weights.yaml に書き戻す（コメントは保持されない点に注意）。"""
    with open(config_dir / "weights.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(weights, f, allow_unicode=True, sort_keys=False)


def save_chains(chains: dict[str, Any], config_dir: Path = CONFIG_DIR) -> None:
    with open(config_dir / "chains.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(chains, f, allow_unicode=True, sort_keys=False)
