"""Entry point for the Jetson runtime application."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Jetson SLAM application.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/jetson/default.yaml"),
        help="Path to the Jetson runtime configuration file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Jetson application scaffold is ready. Config: {args.config}")


if __name__ == "__main__":
    main()
