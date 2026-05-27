#!/usr/bin/env python3
"""Summarize ORB-SLAM3 run outputs."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def parse_log(log_path: Path) -> dict[str, object]:
    if not log_path.exists():
        return {
            "images": "",
            "median_tracking_time": "",
            "mean_tracking_time": "",
            "map_init": "",
        }

    text = log_path.read_text(encoding="utf-8", errors="replace")
    images = re.search(r"Images in the sequence:\s+(\d+)", text)
    median = re.search(r"median tracking time:\s+([0-9.]+)", text)
    mean = re.search(r"mean tracking time:\s+([0-9.]+)", text)
    map_init = "yes" if "New Map created" in text else "no"
    return {
        "images": images.group(1) if images else "",
        "median_tracking_time": median.group(1) if median else "",
        "mean_tracking_time": mean.group(1) if mean else "",
        "map_init": map_init,
    }


def count_trajectory_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, default=Path("results/orbslam3_monocular"))
    parser.add_argument("--output", type=Path, default=Path("results/orbslam3_monocular/summary.csv"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    for result_dir in sorted(path for path in args.results_root.iterdir() if path.is_dir()):
        trajectory = result_dir / "KeyFrameTrajectory.txt"
        log_values = parse_log(result_dir / "run.log")
        rows.append(
            {
                "sequence": result_dir.name,
                "trajectory_exists": trajectory.exists(),
                "keyframes": count_trajectory_rows(trajectory),
                **log_values,
            }
        )

    fieldnames = [
        "sequence",
        "trajectory_exists",
        "keyframes",
        "images",
        "map_init",
        "median_tracking_time",
        "mean_tracking_time",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
