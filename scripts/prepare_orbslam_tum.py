#!/usr/bin/env python3
"""Prepare extracted frames for ORB-SLAM3's mono_tum example."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def iter_sequences(frames_root: Path):
    for frames_csv in sorted(frames_root.rglob("frames.csv")):
        yield frames_csv.parent


def read_frame_rows(sequence_dir: Path) -> list[dict[str, str]]:
    with (sequence_dir / "frames.csv").open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_rgb_txt(sequence_dir: Path, frames_root: Path, output_root: Path) -> Path:
    relative_sequence = sequence_dir.relative_to(frames_root)
    output_sequence_dir = output_root / relative_sequence
    output_sequence_dir.mkdir(parents=True, exist_ok=True)

    rows = read_frame_rows(sequence_dir)
    rgb_txt = output_sequence_dir / "rgb.txt"

    relative_frames_dir = Path("../../..") / frames_root.name / relative_sequence
    with rgb_txt.open("w", encoding="utf-8") as out:
        out.write("# color images\n")
        out.write("# file: generated from extracted frames\n")
        out.write("# timestamp filename\n")
        for row in rows:
            image_path = relative_frames_dir / row["frame_file"]
            out.write(f"{row['timestamp_sec']} {image_path.as_posix()}\n")

    return rgb_txt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-root", type=Path, default=Path("data/interim/frames_10fps"))
    parser.add_argument("--output-root", type=Path, default=Path("data/interim/orbslam_tum_10fps"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_files = [
        write_rgb_txt(sequence_dir, args.frames_root, args.output_root)
        for sequence_dir in iter_sequences(args.frames_root)
    ]
    print(f"Wrote {len(output_files)} ORB-SLAM3 TUM rgb.txt files to {args.output_root}")


if __name__ == "__main__":
    main()
