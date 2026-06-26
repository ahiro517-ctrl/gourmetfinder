"""コマンドラインエントリポイント。

使い方:
  python -m gourmetfinder              # 本番実行（API・スプレッドシート連携）
  python -m gourmetfinder --dry-run    # 動作確認（API不要・fixturesを使用）
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config as cfgmod
from . import pipeline

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="取材候補ソーシング")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="API・スプレッドシートを使わず、サンプルデータで動作確認する",
    )
    parser.add_argument(
        "--fixture",
        default=str(ROOT / "fixtures" / "sample_places.json"),
        help="ドライラン用のサンプルデータ",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "fixtures" / "dry_run_output.csv"),
        help="ドライランの出力CSV",
    )
    args = parser.parse_args(argv)

    settings = cfgmod.load_settings()

    if args.dry_run:
        pipeline.run_dry(settings, Path(args.fixture), Path(args.out))
        return 0

    result = pipeline.run(settings)
    print("実行結果:", result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
