#!/usr/bin/env python3
"""SLAM前に分かる画像品質・特徴点対応・二視点幾何を評価します。

ORB-SLAM3を実行する前段階で、動画がVisual SLAMに向いているかを調べるための
スクリプトです。特徴点数、特徴点分布、マッチ数、RANSAC inlier数、通信量概算を
まとめてCSVに出します。
"""

from __future__ import annotations

import argparse
import csv
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


def read_gray(path: Path, resize_scale: float) -> np.ndarray | None:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None
    if resize_scale == 1.0:
        return image
    height, width = image.shape[:2]
    size = (max(1, round(width * resize_scale)), max(1, round(height * resize_scale)))
    interpolation = cv2.INTER_AREA if resize_scale < 1.0 else cv2.INTER_LINEAR
    return cv2.resize(image, size, interpolation=interpolation)


def image_quality(gray: np.ndarray | None) -> dict[str, float]:
    # 明るさ、コントラスト、ブレの少なさを数値化し、SLAMが失敗しやすい条件を探します。
    if gray is None:
        return {
            "brightness": 0.0,
            "contrast": 0.0,
            "sharpness_laplacian_var": 0.0,
            "gradient_mean": 0.0,
        }
    gray_float = gray.astype(np.float32)
    grad_x = cv2.Sobel(gray_float, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray_float, cv2.CV_32F, 0, 1, ksize=3)
    gradient = cv2.magnitude(grad_x, grad_y)
    return {
        "brightness": round(float(gray_float.mean()), 3),
        "contrast": round(float(gray_float.std()), 3),
        "sharpness_laplacian_var": round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 3),
        "gradient_mean": round(float(gradient.mean()), 3),
    }


def keypoint_distribution(
    keypoints: tuple[cv2.KeyPoint, ...],
    width: int,
    height: int,
    grid_rows: int,
    grid_cols: int,
) -> dict[str, float]:
    # 特徴点が画像全体に散っているかを評価します。
    # 一部に偏ると、マッチ数が多くても姿勢推定には弱くなる可能性があります。
    if not keypoints or width <= 0 or height <= 0:
        return {
            "occupied_grid_ratio": 0.0,
            "grid_entropy": 0.0,
            "max_cell_ratio": 0.0,
            "centroid_x_norm": 0.0,
            "centroid_y_norm": 0.0,
        }

    counts = np.zeros((grid_rows, grid_cols), dtype=np.float32)
    xs: list[float] = []
    ys: list[float] = []
    for keypoint in keypoints:
        x, y = keypoint.pt
        xs.append(float(x))
        ys.append(float(y))
        col = min(grid_cols - 1, max(0, int(x / width * grid_cols)))
        row = min(grid_rows - 1, max(0, int(y / height * grid_rows)))
        counts[row, col] += 1

    total = float(len(keypoints))
    probabilities = counts[counts > 0] / total
    entropy = -float(np.sum(probabilities * np.log2(probabilities))) if probabilities.size else 0.0
    max_entropy = float(np.log2(grid_rows * grid_cols)) if grid_rows * grid_cols > 1 else 1.0
    return {
        "occupied_grid_ratio": round(float(np.count_nonzero(counts) / counts.size), 4),
        "grid_entropy": round(entropy / max_entropy, 4) if max_entropy else 0.0,
        "max_cell_ratio": round(float(counts.max() / total), 4),
        "centroid_x_norm": round(float(np.mean(xs) / width), 4),
        "centroid_y_norm": round(float(np.mean(ys) / height), 4),
    }


def pair_indices(frame_count: int, frame_step: int, max_pairs: int) -> list[int]:
    if frame_count <= frame_step:
        return []
    indices = list(range(0, frame_count - frame_step))
    if max_pairs <= 0 or len(indices) <= max_pairs:
        return indices
    sampled = np.linspace(0, len(indices) - 1, max_pairs, dtype=int)
    return [indices[index] for index in sorted(set(sampled.tolist()))]


def estimate_geometry(
    keypoints_a: tuple[cv2.KeyPoint, ...],
    keypoints_b: tuple[cv2.KeyPoint, ...],
    matches: list[cv2.DMatch],
) -> dict[str, float]:
    # Homographyは平面運動に近い対応、Fundamental matrixは一般的な二視点幾何の対応を見ます。
    # 本研究では特に、Fundamental matrixのinlier数を「相対位置推定に使えそうな対応点数」として扱います。
    distances = [float(match.distance) for match in matches]
    result = {
        "avg_match_distance": safe_mean(distances),
        "fundamental_inliers": 0,
        "fundamental_inlier_ratio": 0.0,
        "homography_inliers": 0,
        "homography_inlier_ratio": 0.0,
    }
    if len(matches) < 4:
        return result

    points_a = np.float32([keypoints_a[match.queryIdx].pt for match in matches])
    points_b = np.float32([keypoints_b[match.trainIdx].pt for match in matches])

    try:
        homography, homography_mask = cv2.findHomography(points_a, points_b, cv2.RANSAC, 3.0)
        if homography is not None and homography_mask is not None:
            inliers = int(homography_mask.ravel().sum())
            result["homography_inliers"] = inliers
            result["homography_inlier_ratio"] = safe_ratio(inliers, len(matches))
    except cv2.error:
        pass

    if len(matches) < 8:
        return result

    try:
        fundamental, fundamental_mask = cv2.findFundamentalMat(
            points_a,
            points_b,
            cv2.FM_RANSAC,
            1.0,
            0.99,
        )
        if fundamental is not None and fundamental_mask is not None:
            inliers = int(fundamental_mask.ravel().sum())
            result["fundamental_inliers"] = inliers
            result["fundamental_inlier_ratio"] = safe_ratio(inliers, len(matches))
    except cv2.error:
        pass

    return result


def summarize(rows: list[dict[str, object]], keys: list[str]) -> list[dict[str, object]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row[key] for key in keys), []).append(row)

    summary_rows: list[dict[str, object]] = []
    numeric_columns = [
        "keypoints_a",
        "keypoints_b",
        "occupied_grid_ratio_a",
        "occupied_grid_ratio_b",
        "grid_entropy_a",
        "grid_entropy_b",
        "brightness_mean",
        "contrast_mean",
        "sharpness_laplacian_var_mean",
        "gradient_mean",
        "matches",
        "good_matches",
        "good_match_ratio",
        "avg_match_distance",
        "fundamental_inliers",
        "fundamental_inlier_ratio",
        "homography_inliers",
        "homography_inlier_ratio",
        "compact_packet_bytes_per_frame",
        "jpeg_bytes_per_frame",
        "compact_packet_vs_jpeg_ratio",
    ]

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
    nfeatures: int,
    frame_steps: list[int],
    resize_scales: list[float],
    good_match_distance: int,
    grid_rows: int,
    grid_cols: int,
    max_pairs: int,
) -> list[dict[str, object]]:
    sequence = sequence_name(sequence_dir, frames_root)
    frame_paths = sorted(sequence_dir.glob("frame_*.jpg"))
    rows: list[dict[str, object]] = []

    for resize_scale in resize_scales:
        orb = cv2.ORB_create(nfeatures=nfeatures)
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        cache: dict[Path, tuple[np.ndarray | None, tuple[cv2.KeyPoint, ...], np.ndarray | None, dict[str, float]]] = {}

        for frame_path in tqdm(frame_paths, desc=f"{sequence} scale={resize_scale}", unit="frame"):
            gray = read_gray(frame_path, resize_scale)
            if gray is None:
                keypoints: tuple[cv2.KeyPoint, ...] = tuple()
                descriptors = None
            else:
                detected, descriptors = orb.detectAndCompute(gray, None)
                keypoints = tuple(detected)
            cache[frame_path] = (gray, keypoints, descriptors, image_quality(gray))

        for frame_step in frame_steps:
            for pair_index, start_index in enumerate(pair_indices(len(frame_paths), frame_step, max_pairs)):
                frame_a = frame_paths[start_index]
                frame_b = frame_paths[start_index + frame_step]
                gray_a, keypoints_a, descriptors_a, quality_a = cache[frame_a]
                gray_b, keypoints_b, descriptors_b, quality_b = cache[frame_b]
                height, width = gray_a.shape[:2] if gray_a is not None else (0, 0)

                if descriptors_a is None or descriptors_b is None:
                    matches: list[cv2.DMatch] = []
                else:
                    matches = list(matcher.match(descriptors_a, descriptors_b))
                    matches.sort(key=lambda match: match.distance)

                good_matches = [match for match in matches if match.distance <= good_match_distance]
                geometry = estimate_geometry(keypoints_a, keypoints_b, matches)
                distribution_a = keypoint_distribution(keypoints_a, width, height, grid_rows, grid_cols)
                distribution_b = keypoint_distribution(keypoints_b, width, height, grid_rows, grid_cols)
                # 1フレームあたりの特徴量パケットサイズを概算し、JPEG画像サイズと比較します。
                compact_packet_bytes_per_frame = (
                    (len(keypoints_a) + len(keypoints_b))
                    * (ORB_DESCRIPTOR_BYTES + COMPACT_KEYPOINT_BYTES)
                    / 2.0
                )
                jpeg_bytes_per_frame = (frame_a.stat().st_size + frame_b.stat().st_size) / 2.0

                rows.append(
                    {
                        "sequence": sequence,
                        "group": sequence_group(sequence),
                        "nfeatures": nfeatures,
                        "resize_scale": resize_scale,
                        "frame_step": frame_step,
                        "pair_index": pair_index,
                        "frame_a": frame_a.name,
                        "frame_b": frame_b.name,
                        "width": width,
                        "height": height,
                        "keypoints_a": len(keypoints_a),
                        "keypoints_b": len(keypoints_b),
                        "occupied_grid_ratio_a": distribution_a["occupied_grid_ratio"],
                        "occupied_grid_ratio_b": distribution_b["occupied_grid_ratio"],
                        "grid_entropy_a": distribution_a["grid_entropy"],
                        "grid_entropy_b": distribution_b["grid_entropy"],
                        "max_cell_ratio_a": distribution_a["max_cell_ratio"],
                        "max_cell_ratio_b": distribution_b["max_cell_ratio"],
                        "brightness_mean": safe_mean([quality_a["brightness"], quality_b["brightness"]]),
                        "contrast_mean": safe_mean([quality_a["contrast"], quality_b["contrast"]]),
                        "sharpness_laplacian_var_mean": safe_mean(
                            [quality_a["sharpness_laplacian_var"], quality_b["sharpness_laplacian_var"]]
                        ),
                        "gradient_mean": safe_mean([quality_a["gradient_mean"], quality_b["gradient_mean"]]),
                        "matches": len(matches),
                        "good_matches": len(good_matches),
                        "good_match_ratio": safe_ratio(len(good_matches), len(matches)),
                        "avg_match_distance": geometry["avg_match_distance"],
                        "fundamental_inliers": geometry["fundamental_inliers"],
                        "fundamental_inlier_ratio": geometry["fundamental_inlier_ratio"],
                        "homography_inliers": geometry["homography_inliers"],
                        "homography_inlier_ratio": geometry["homography_inlier_ratio"],
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
    parser.add_argument("--output-dir", type=Path, default=Path("results/preslam_geometry"))
    parser.add_argument("--nfeatures", type=int, default=1000)
    parser.add_argument("--frame-steps", type=int, nargs="+", default=[1, 3, 5, 10])
    parser.add_argument("--resize-scales", type=float, nargs="+", default=[1.0, 0.5])
    parser.add_argument("--good-match-distance", type=int, default=GOOD_MATCH_DISTANCE)
    parser.add_argument("--grid-rows", type=int, default=4)
    parser.add_argument("--grid-cols", type=int, default=4)
    parser.add_argument(
        "--max-pairs-per-sequence",
        type=int,
        default=0,
        help="Use 0 to evaluate all available pairs for each frame step.",
    )
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
                args.nfeatures,
                args.frame_steps,
                args.resize_scales,
                args.good_match_distance,
                args.grid_rows,
                args.grid_cols,
                args.max_pairs_per_sequence,
            )
        )

    sequence_summary = summarize(rows, ["sequence", "group", "nfeatures", "resize_scale", "frame_step"])
    group_summary = summarize(rows, ["group", "nfeatures", "resize_scale", "frame_step"])
    # pair_metrics は詳細確認用、summary/group_summary は先生への説明やグラフ作成に使う要約です。
    write_csv(args.output_dir / "pair_metrics.csv", rows)
    write_csv(args.output_dir / "summary.csv", sequence_summary)
    write_csv(args.output_dir / "group_summary.csv", group_summary)
    print(f"Wrote {len(rows)} pair rows to {args.output_dir}")


if __name__ == "__main__":
    main()
