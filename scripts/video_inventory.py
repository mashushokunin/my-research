#!/usr/bin/env python3
"""Create a CSV inventory for research video files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2


VIDEO_EXTENSIONS = {".avi", ".mkv", ".mov", ".mp4"}


def iter_videos(data_root: Path):
    ignored_parts = {"interim", "processed", "sample"}
    for path in sorted(data_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if any(part in ignored_parts for part in path.relative_to(data_root).parts):
            continue
        yield path


def read_video_metadata(path: Path) -> dict[str, object]:
    cap = cv2.VideoCapture(str(path))
    opened = cap.isOpened()

    fps = cap.get(cv2.CAP_PROP_FPS) if opened else 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) if opened else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if opened else 0
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if opened else 0
    duration_sec = frame_count / fps if fps > 0 else 0.0

    cap.release()

    return {
        "openable": opened,
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "frame_count": frame_count,
        "duration_sec": round(duration_sec, 3),
    }


def build_row(path: Path, data_root: Path) -> dict[str, object]:
    relative = path.relative_to(data_root)
    group = relative.parts[0] if len(relative.parts) > 1 else ""
    metadata = read_video_metadata(path)

    return {
        "path": str(relative),
        "group": group,
        "stem": path.stem,
        "suffix": path.suffix,
        "size_bytes": path.stat().st_size,
        **metadata,
        "privacy_checked": "",
        "quality_note": "",
        "experiment_note": "",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/metadata/video_inventory.csv"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_root = args.data_root
    rows = [build_row(path, data_root) for path in iter_videos(data_root)]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "path",
        "group",
        "stem",
        "suffix",
        "size_bytes",
        "openable",
        "width",
        "height",
        "fps",
        "frame_count",
        "duration_sec",
        "privacy_checked",
        "quality_note",
        "experiment_note",
    ]

    with args.output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
