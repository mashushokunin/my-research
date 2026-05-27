#!/usr/bin/env python3
"""Compute a simple ORB feature baseline from extracted video frames."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
from tqdm import tqdm


def iter_sequences(frames_root: Path):
    for metadata_path in sorted(frames_root.rglob("metadata.json")):
        yield metadata_path.parent


def sequence_name(sequence_dir: Path, frames_root: Path) -> str:
    return str(sequence_dir.relative_to(frames_root))


def analyze_sequence(
    sequence_dir: Path,
    frames_root: Path,
    orb: cv2.ORB,
    matcher: cv2.BFMatcher,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    frame_paths = sorted(sequence_dir.glob("frame_*.jpg"))
    frame_rows: list[dict[str, object]] = []
    match_counts: list[int] = []
    previous_descriptors = None
    sequence = sequence_name(sequence_dir, frames_root)

    for index, frame_path in enumerate(tqdm(frame_paths, desc=sequence, unit="frame")):
        image = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            keypoint_count = 0
            match_count = 0
            descriptors = None
        else:
            keypoints, descriptors = orb.detectAndCompute(image, None)
            keypoint_count = len(keypoints)
            if previous_descriptors is None or descriptors is None:
                match_count = 0
            else:
                matches = matcher.match(previous_descriptors, descriptors)
                match_count = len(matches)

        if index > 0:
            match_counts.append(match_count)

        frame_rows.append(
            {
                "sequence": sequence,
                "frame_file": frame_path.name,
                "frame_index": index,
                "keypoints": keypoint_count,
                "descriptor_bytes": keypoint_count * 32,
                "matches_to_previous": match_count,
            }
        )
        previous_descriptors = descriptors

    keypoint_counts = [int(row["keypoints"]) for row in frame_rows]
    summary = {
        "sequence": sequence,
        "frames": len(frame_rows),
        "nfeatures": int(orb.getMaxFeatures()),
        "avg_keypoints": round(sum(keypoint_counts) / len(keypoint_counts), 3)
        if keypoint_counts
        else 0,
        "min_keypoints": min(keypoint_counts) if keypoint_counts else 0,
        "max_keypoints": max(keypoint_counts) if keypoint_counts else 0,
        "avg_descriptor_bytes_per_frame": round(
            sum(count * 32 for count in keypoint_counts) / len(keypoint_counts),
            3,
        )
        if keypoint_counts
        else 0,
        "avg_matches_to_previous": round(sum(match_counts) / len(match_counts), 3)
        if match_counts
        else 0,
        "min_matches_to_previous": min(match_counts) if match_counts else 0,
        "max_matches_to_previous": max(match_counts) if match_counts else 0,
    }
    return frame_rows, summary


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-root", type=Path, default=Path("data/interim/frames"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/orb_baseline"))
    parser.add_argument("--nfeatures", type=int, default=1000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    orb = cv2.ORB_create(nfeatures=args.nfeatures)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    all_frame_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for sequence_dir in iter_sequences(args.frames_root):
        frame_rows, summary = analyze_sequence(
            sequence_dir,
            args.frames_root,
            orb,
            matcher,
        )
        all_frame_rows.extend(frame_rows)
        summary_rows.append(summary)

    write_csv(
        args.output_dir / "frame_metrics.csv",
        all_frame_rows,
        [
            "sequence",
            "frame_file",
            "frame_index",
            "keypoints",
            "descriptor_bytes",
            "matches_to_previous",
        ],
    )
    write_csv(
        args.output_dir / "sequence_summary.csv",
        summary_rows,
        [
            "sequence",
            "frames",
            "nfeatures",
            "avg_keypoints",
            "min_keypoints",
            "max_keypoints",
            "avg_descriptor_bytes_per_frame",
            "avg_matches_to_previous",
            "min_matches_to_previous",
            "max_matches_to_previous",
        ],
    )
    print(f"Wrote ORB baseline metrics to {args.output_dir}")


if __name__ == "__main__":
    main()
