"""Entry point for the Jetson runtime application."""

from __future__ import annotations

import argparse
from pathlib import Path

from runtime.config import load_config
from runtime.runner import JetsonRuntime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Jetson SLAM application.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/jetson/default.yaml"),
        help="Path to the Jetson runtime configuration file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and validate the configuration without opening the camera.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # YAMLを読み込み、相対パスをリポジトリ基準の絶対パスへ解決した設定オブジェクトにします。
    config = load_config(args.config)
    if args.dry_run:
        # Jetson上でカメラを開く前に、設定が正しく読めるかだけ確認するためのモードです。
        print(f"Loaded Jetson config: {args.config}")
        print(config)
        return

    # 実際の処理はJetsonRuntimeへ委譲します。
    # main.py は起動入口に限定し、カメラ処理や保存処理は runtime/ 側に分けています。
    runtime = JetsonRuntime(config)
    runtime.run()


if __name__ == "__main__":
    main()
