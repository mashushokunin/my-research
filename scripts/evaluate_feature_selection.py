#!/usr/bin/env python3
"""Compare feature selection strategies under communication budgets."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from statistics import mean
from typing import Iterable

import cv2
import numpy as np
from tqdm import tqdm


ORB_DESCRIPTOR_BYTES = 32
COMPACT_KEYPOINT_BYTES = 9
GOOD_MATCH_DISTANCE = 64


def iter_sequences(frames_root: Path) -> Iterable[Path]:
    for metadata_path in sorted(frames_root.rglob("metadata.json")):
        yield metadata_path.parent


def sequence_name(sequence_dir: Path, frames_root: Path) -> str:
    return sequence_dir.relative_to(frames_root).as_posix()


def sequence_group(sequence: str) -> str:
    return sequence.split("/", 1)[0] if "/" in sequence else "ungrouped"


def safe_mean(values: list[float]) -> float:
    return round(mean(values), 3) if values else 0.0


def safe_ratio(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def pair_indices(frame_count: int, frame_step: int, max_pairs: int) -> list[int]:
    if frame_count <= frame_step:
        return []
    indices = list(range(0, frame_count - frame_step))
    if max_pairs <= 0 or len(indices) <= max_pairs:
        return indices
    sampled = np.linspace(0, len(indices) - 1, max_pairs, dtype=int)
    return [indices[index] for index in sorted(set(sampled.tolist()))]


def select_top_response(keypoints: tuple[cv2.KeyPoint, ...], budget: int) -> list[int]:
    return sorted(range(len(keypoints)), key=lambda index: keypoints[index].response, reverse=True)[:budget]


def select_random(keypoints: tuple[cv2.KeyPoint, ...], budget: int, seed: str) -> list[int]:
    indices = list(range(len(keypoints)))
    rng = random.Random(seed)
    rng.shuffle(indices)
    return indices[:budget]


def select_grid(
    keypoints: tuple[cv2.KeyPoint, ...],
    budget: int,
    width: int,
    height: int,
    grid_rows: int,
    grid_cols: int,
) -> list[int]:
    cells: list[list[int]] = [[] for _ in range(grid_rows * grid_cols)]
    for index, keypoint in enumerate(keypoints):
        x, y = keypoint.pt
        col = min(grid_cols - 1, max(0, int(x / width * grid_cols))) if width > 0 else 0
        row = min(grid_rows - 1, max(0, int(y / height * grid_rows))) if height > 0 else 0
        cells[row * grid_cols + col].append(index)

    for cell in cells:
        cell.sort(key=lambda index: keypoints[index].response, reverse=True)

    selected: list[int] = []
    cursor = 0
    while len(selected) < budget:
        added = False
        for cell in cells:
            if cursor < len(cell):
                selected.append(cell[cursor])
                added = True
                if len(selected) >= budget:
                    break
        if not added:
            break
        cursor += 1

    return selected


def selected_descriptors(
    descriptors: np.ndarray | None,
    selected_indices: list[int],
) -> np.ndarray | None:
    if descriptors is None or not selected_indices:
        return None
    return descriptors[np.asarray(selected_indices, dtype=np.int32)]


def estimate_fundamental_inliers(
    keypoints_a: tuple[cv2.KeyPoint, ...],
    keypoints_b: tuple[cv2.KeyPoint, ...],
    selected_a: list[int],
    selected_b: list[int],
    matches: list[cv2.DMatch],
) -> tuple[int, float]:
    if len(matches) < 8:
        return 0, 0.0

    points_a = np.float32([keypoints_a[selected_a[match.queryIdx]].pt for match in matches])
    points_b = np.float32([keypoints_b[selected_b[match.trainIdx]].pt for match in matches])
    try:
        fundamental, mask = cv2.findFundamentalMat(points_a, points_b, cv2.FM_RANSAC, 1.0, 0.99)
    except cv2.error:
        return 0, 0.0
    if fundamental is None or mask is None:
        return 0, 0.0
    inliers = int(mask.ravel().sum())
    return inliers, safe_ratio(inliers, len(matches))


def select_indices(
    strategy: str,
    keypoints: tuple[cv2.KeyPoint, ...],
    budget: int,
    width: int,
    height: int,
    grid_rows: int,
    grid_cols: int,
    seed: str,
) -> list[int]:
    budget = min(budget, len(keypoints))
    if budget <= 0:
        return []
    if strategy == "top_response":
        return select_top_response(keypoints, budget)
    if strategy == "grid":
        return select_grid(keypoints, budget, width, height, grid_rows, grid_cols)
    if strategy == "random":
        return select_random(keypoints, budget, seed)
    raise ValueError(f"Unknown strategy: {strategy}")


def summarize(rows: list[dict[str, object]], keys: list[str]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row[key] for key in keys), []).append(row)

    numeric_columns = [
        "selected_a",
        "selected_b",
        "matches",
        "good_matches",
        "good_match_ratio",
        "avg_match_distance",
        "fundamental_inliers",
        "fundamental_inlier_ratio",
        "compact_packet_bytes_per_frame",
        "jpeg_bytes_per_frame",
        "compact_packet_vs_jpeg_ratio",
    ]
    summary_rows: list[dict[str, object]] = []
    for key_values, group_rows in sorted(grouped.items()):
        summary = {key: value for key, value in zip(keys, key_values)}
        summary["pairs"] = len(group_rows)
        for column in numeric_columns:
            summary[f"avg_{column}"] = safe_mean([float(row[column]) for row in group_rows])
        summary_rows.append(summary)
    return summary_rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def evaluate_sequence(
    sequence_dir: Path,
    frames_root: Path,
    detect_nfeatures: int,
    budgets: list[int],
    strategies: list[str],
    frame_step: int,
    max_pairs: int,
    random_repeats: int,
    good_match_distance: int,
    grid_rows: int,
    grid_cols: int,
    seed: int,
) -> list[dict[str, object]]:
    sequence = sequence_name(sequence_dir, frames_root)
    frame_paths = sorted(sequence_dir.glob("frame_*.jpg"))
    orb = cv2.ORB_create(nfeatures=detect_nfeatures)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    cache: dict[Path, tuple[int, int, tuple[cv2.KeyPoint, ...], np.ndarray | None]] = {}

    for frame_path in tqdm(frame_paths, desc=f"{sequence} detect", unit="frame"):
        gray = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
        if gray is None:
            cache[frame_path] = (0, 0, tuple(), None)
            continue
        keypoints, descriptors = orb.detectAndCompute(gray, None)
        height, width = gray.shape[:2]
        cache[frame_path] = (width, height, tuple(keypoints), descriptors)

    rows: list[dict[str, object]] = []
    for start_index in pair_indices(len(frame_paths), frame_step, max_pairs):
        frame_a = frame_paths[start_index]
        frame_b = frame_paths[start_index + frame_step]
        width_a, height_a, keypoints_a, descriptors_a = cache[frame_a]
        width_b, height_b, keypoints_b, descriptors_b = cache[frame_b]

        for budget in budgets:
            for strategy in strategies:
                repeats = random_repeats if strategy == "random" else 1
                for repeat in range(repeats):
                    selected_a = select_indices(
                        strategy,
                        keypoints_a,
                        budget,
                        width_a,
                        height_a,
                        grid_rows,
                        grid_cols,
                        f"{seed}:{sequence}:{frame_a.name}:{budget}:{strategy}:{repeat}",
                    )
                    selected_b = select_indices(
                        strategy,
                        keypoints_b,
                        budget,
                        width_b,
                        height_b,
                        grid_rows,
                        grid_cols,
                        f"{seed}:{sequence}:{frame_b.name}:{budget}:{strategy}:{repeat}",
                    )
                    selected_descriptors_a = selected_descriptors(descriptors_a, selected_a)
                    selected_descriptors_b = selected_descriptors(descriptors_b, selected_b)
                    if selected_descriptors_a is None or selected_descriptors_b is None:
                        matches: list[cv2.DMatch] = []
                    else:
                        matches = list(matcher.match(selected_descriptors_a, selected_descriptors_b))
                        matches.sort(key=lambda match: match.distance)

                    distances = [float(match.distance) for match in matches]
                    good_matches = [match for match in matches if match.distance <= good_match_distance]
                    fundamental_inliers, fundamental_inlier_ratio = estimate_fundamental_inliers(
                        keypoints_a,
                        keypoints_b,
                        selected_a,
                        selected_b,
                        matches,
                    )
                    compact_packet_bytes_per_frame = (
                        (len(selected_a) + len(selected_b))
                        * (ORB_DESCRIPTOR_BYTES + COMPACT_KEYPOINT_BYTES)
                        / 2.0
                    )
                    jpeg_bytes_per_frame = (frame_a.stat().st_size + frame_b.stat().st_size) / 2.0

                    rows.append(
                        {
                            "sequence": sequence,
                            "group": sequence_group(sequence),
                            "detect_nfeatures": detect_nfeatures,
                            "frame_step": frame_step,
                            "budget": budget,
                            "strategy": strategy,
                            "repeat": repeat,
                            "frame_a": frame_a.name,
                            "frame_b": frame_b.name,
                            "detected_a": len(keypoints_a),
                            "detected_b": len(keypoints_b),
                            "selected_a": len(selected_a),
                            "selected_b": len(selected_b),
                            "matches": len(matches),
                            "good_matches": len(good_matches),
                            "good_match_ratio": safe_ratio(len(good_matches), len(matches)),
                            "avg_match_distance": safe_mean(distances),
                            "fundamental_inliers": fundamental_inliers,
                            "fundamental_inlier_ratio": fundamental_inlier_ratio,
                            "compact_packet_bytes_per_frame": round(compact_packet_bytes_per_frame, 3),
                            "jpeg_bytes_per_frame": round(jpeg_bytes_per_frame, 3),
                            "compact_packet_vs_jpeg_ratio": safe_ratio(
                                compact_packet_bytes_per_frame,
                                jpeg_bytes_per_frame,
                            ),
                        }
                    )

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-root", type=Path, default=Path("data/interim/frames_10fps"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/feature_selection"))
    parser.add_argument("--detect-nfeatures", type=int, default=2000)
    parser.add_argument("--budgets", type=int, nargs="+", default=[100, 250, 500, 1000])
    parser.add_argument("--strategies", nargs="+", default=["top_response", "grid", "random"])
    parser.add_argument("--frame-step", type=int, default=1)
    parser.add_argument(
        "--max-pairs-per-sequence",
        type=int,
        default=0,
        help="Use 0 to evaluate all available adjacent pairs.",
    )
    parser.add_argument("--random-repeats", type=int, default=3)
    parser.add_argument("--good-match-distance", type=int, default=GOOD_MATCH_DISTANCE)
    parser.add_argument("--grid-rows", type=int, default=4)
    parser.add_argument("--grid-cols", type=int, default=4)
    parser.add_argument("--seed", type=int, default=13)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sequence_dirs = list(iter_sequences(args.frames_root))
    if not sequence_dirs:
        raise FileNotFoundError(f"No extracted frame sequences found under {args.frames_root}")

    rows: list[dict[str, object]] = []
    for sequence_dir in sequence_dirs:
        rows.extend(
            evaluate_sequence(
                sequence_dir,
                args.frames_root,
                args.detect_nfeatures,
                args.budgets,
                args.strategies,
                args.frame_step,
                args.max_pairs_per_sequence,
                args.random_repeats,
                args.good_match_distance,
                args.grid_rows,
                args.grid_cols,
                args.seed,
            )
        )

    sequence_summary = summarize(rows, ["sequence", "group", "detect_nfeatures", "frame_step", "budget", "strategy"])
    group_summary = summarize(rows, ["group", "detect_nfeatures", "frame_step", "budget", "strategy"])
    write_csv(args.output_dir / "pair_metrics.csv", rows)
    write_csv(args.output_dir / "summary.csv", sequence_summary)
    write_csv(args.output_dir / "group_summary.csv", group_summary)
    print(f"Wrote {len(rows)} feature selection rows to {args.output_dir}")


if __name__ == "__main__":
    main()
