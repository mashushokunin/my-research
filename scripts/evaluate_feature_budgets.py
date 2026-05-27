#!/usr/bin/env python3
"""Evaluate ORB feature budgets for communication-efficient Visual SLAM."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean

import cv2
from tqdm import tqdm


ORB_DESCRIPTOR_BYTES = 32
COMPACT_KEYPOINT_BYTES = 9
FLOAT_KEYPOINT_BYTES = 24
GOOD_MATCH_DISTANCE = 64


def iter_sequences(frames_root: Path):
    for metadata_path in sorted(frames_root.rglob("metadata.json")):
        yield metadata_path.parent


def sequence_name(sequence_dir: Path, frames_root: Path) -> str:
    return sequence_dir.relative_to(frames_root).as_posix()


def safe_mean(values: list[float]) -> float:
    return round(mean(values), 3) if values else 0.0


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * pct)
    return round(ordered[index], 3)


def analyze_sequence(
    sequence_dir: Path,
    frames_root: Path,
    nfeatures: int,
    good_match_distance: int,
) -> dict[str, object]:
    orb = cv2.ORB_create(nfeatures=nfeatures)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    frame_paths = sorted(sequence_dir.glob("frame_*.jpg"))
    keypoint_counts: list[int] = []
    match_counts: list[int] = []
    good_match_counts: list[int] = []
    match_distances: list[float] = []
    jpeg_sizes = [path.stat().st_size for path in frame_paths]
    previous_descriptors = None

    for frame_path in tqdm(
        frame_paths,
        desc=f"{sequence_name(sequence_dir, frames_root)} n={nfeatures}",
        unit="frame",
    ):
        image = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            descriptors = None
            keypoint_counts.append(0)
        else:
            keypoints, descriptors = orb.detectAndCompute(image, None)
            keypoint_counts.append(len(keypoints))

        if previous_descriptors is not None and descriptors is not None:
            matches = matcher.match(previous_descriptors, descriptors)
            distances = [match.distance for match in matches]
            match_counts.append(len(matches))
            good_match_counts.append(sum(distance <= good_match_distance for distance in distances))
            match_distances.extend(distances)
        elif previous_descriptors is not None:
            match_counts.append(0)
            good_match_counts.append(0)

        previous_descriptors = descriptors

    avg_keypoints = safe_mean([float(count) for count in keypoint_counts])
    descriptor_bytes = [count * ORB_DESCRIPTOR_BYTES for count in keypoint_counts]
    compact_packet_bytes = [
        count * (ORB_DESCRIPTOR_BYTES + COMPACT_KEYPOINT_BYTES) for count in keypoint_counts
    ]
    float_packet_bytes = [
        count * (ORB_DESCRIPTOR_BYTES + FLOAT_KEYPOINT_BYTES) for count in keypoint_counts
    ]
    avg_jpeg_bytes = safe_mean([float(size) for size in jpeg_sizes])
    avg_compact_packet = safe_mean([float(size) for size in compact_packet_bytes])

    return {
        "sequence": sequence_name(sequence_dir, frames_root),
        "frames": len(frame_paths),
        "nfeatures": nfeatures,
        "avg_keypoints": avg_keypoints,
        "min_keypoints": min(keypoint_counts) if keypoint_counts else 0,
        "p10_keypoints": percentile([float(count) for count in keypoint_counts], 0.10),
        "p90_keypoints": percentile([float(count) for count in keypoint_counts], 0.90),
        "max_keypoints": max(keypoint_counts) if keypoint_counts else 0,
        "avg_matches_to_previous": safe_mean([float(count) for count in match_counts]),
        "avg_good_matches_to_previous": safe_mean([float(count) for count in good_match_counts]),
        "avg_match_distance": safe_mean(match_distances),
        "avg_descriptor_bytes_per_frame": safe_mean([float(size) for size in descriptor_bytes]),
        "avg_compact_packet_bytes_per_frame": avg_compact_packet,
        "avg_float_packet_bytes_per_frame": safe_mean([float(size) for size in float_packet_bytes]),
        "avg_jpeg_bytes_per_frame": avg_jpeg_bytes,
        "compact_packet_vs_jpeg_ratio": round(avg_compact_packet / avg_jpeg_bytes, 4)
        if avg_jpeg_bytes
        else 0.0,
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "sequence",
        "frames",
        "nfeatures",
        "avg_keypoints",
        "min_keypoints",
        "p10_keypoints",
        "p90_keypoints",
        "max_keypoints",
        "avg_matches_to_previous",
        "avg_good_matches_to_previous",
        "avg_match_distance",
        "avg_descriptor_bytes_per_frame",
        "avg_compact_packet_bytes_per_frame",
        "avg_float_packet_bytes_per_frame",
        "avg_jpeg_bytes_per_frame",
        "compact_packet_vs_jpeg_ratio",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-root", type=Path, default=Path("data/interim/frames_10fps"))
    parser.add_argument("--output", type=Path, default=Path("results/feature_budgets/summary.csv"))
    parser.add_argument(
        "--nfeatures",
        type=int,
        nargs="+",
        default=[250, 500, 1000, 2000],
        help="ORB feature budgets to evaluate.",
    )
    parser.add_argument("--good-match-distance", type=int, default=GOOD_MATCH_DISTANCE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows: list[dict[str, object]] = []
    sequence_dirs = list(iter_sequences(args.frames_root))
    for nfeatures in args.nfeatures:
        for sequence_dir in sequence_dirs:
            rows.append(
                analyze_sequence(
                    sequence_dir,
                    args.frames_root,
                    nfeatures,
                    args.good_match_distance,
                )
            )

    write_csv(args.output, rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
