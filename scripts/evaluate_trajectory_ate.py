#!/usr/bin/env python3
"""ORB-SLAM3の推定軌跡とEuRoC ground truthからATE RMSEを計算します。

単眼SLAMではスケールが不定になりやすいため、Sim(3)で推定軌跡をground truthへ
合わせてから、位置誤差のRMSEを計算します。結果はCSVと軌跡図として保存します。
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def normalize_timestamp(value: float) -> float:
    # EuRoCの時刻はナノ秒、ORB-SLAM3の出力は秒の場合があるため秒単位にそろえます。
    return value * 1e-9 if value > 1e12 else value


def read_tum_trajectory(path: Path) -> dict[float, np.ndarray]:
    # ORB-SLAM3のTUM形式軌跡から、ATEに使う位置成分だけを読みます。
    poses: dict[float, np.ndarray] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        timestamp = normalize_timestamp(float(parts[0]))
        poses[timestamp] = np.asarray([float(parts[1]), float(parts[2]), float(parts[3])], dtype=np.float64)
    return poses


def read_euroc_groundtruth(path: Path) -> dict[float, np.ndarray]:
    poses: dict[float, np.ndarray] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if not row or row[0].startswith("#"):
                continue
            if len(row) < 4:
                continue
            timestamp = normalize_timestamp(float(row[0]))
            poses[timestamp] = np.asarray([float(row[1]), float(row[2]), float(row[3])], dtype=np.float64)
    return poses


def associate(
    estimated: dict[float, np.ndarray],
    groundtruth: dict[float, np.ndarray],
    max_diff_sec: float,
) -> tuple[np.ndarray, np.ndarray, list[tuple[float, float]]]:
    # 推定軌跡とground truthは完全に同じ時刻ではないため、最も近い時刻同士を対応付けます。
    gt_times = np.asarray(sorted(groundtruth.keys()), dtype=np.float64)
    pairs: list[tuple[float, float]] = []
    estimated_points: list[np.ndarray] = []
    groundtruth_points: list[np.ndarray] = []

    for est_time in sorted(estimated.keys()):
        if gt_times.size == 0:
            break
        index = int(np.searchsorted(gt_times, est_time))
        candidates = []
        if index < len(gt_times):
            candidates.append(gt_times[index])
        if index > 0:
            candidates.append(gt_times[index - 1])
        if not candidates:
            continue
        gt_time = min(candidates, key=lambda candidate: abs(candidate - est_time))
        if abs(gt_time - est_time) <= max_diff_sec:
            pairs.append((est_time, float(gt_time)))
            estimated_points.append(estimated[est_time])
            groundtruth_points.append(groundtruth[float(gt_time)])

    if not estimated_points:
        return np.empty((0, 3)), np.empty((0, 3)), []
    return np.vstack(estimated_points), np.vstack(groundtruth_points), pairs


def align_sim3(estimated: np.ndarray, groundtruth: np.ndarray) -> tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    # Umeyama法に相当するSim(3)アラインメントです。
    # rotation, translation, scale を推定し、単眼SLAMのスケール不定性を吸収します。
    if estimated.shape[0] < 3:
        raise ValueError("At least three associated poses are required for Sim(3) alignment.")

    source_mean = estimated.mean(axis=0)
    target_mean = groundtruth.mean(axis=0)
    source_centered = estimated - source_mean
    target_centered = groundtruth - target_mean
    covariance = (target_centered.T @ source_centered) / estimated.shape[0]

    u_matrix, singular_values, vt_matrix = np.linalg.svd(covariance)
    correction = np.eye(3)
    if np.linalg.det(u_matrix @ vt_matrix) < 0:
        correction[-1, -1] = -1
    rotation = u_matrix @ correction @ vt_matrix
    variance = float(np.mean(np.sum(source_centered**2, axis=1)))
    scale = float(np.sum(singular_values * np.diag(correction)) / variance) if variance else 1.0
    translation = target_mean - scale * rotation @ source_mean
    aligned = (scale * (rotation @ estimated.T)).T + translation
    return aligned, scale, rotation, translation


def compute_metrics(aligned: np.ndarray, groundtruth: np.ndarray) -> dict[str, float]:
    # ATEは各時刻の位置誤差ノルムから計算します。主にRMSEを代表値として使います。
    errors = np.linalg.norm(aligned - groundtruth, axis=1)
    return {
        "ate_rmse": round(float(np.sqrt(np.mean(errors**2))), 6),
        "ate_mean": round(float(np.mean(errors)), 6),
        "ate_median": round(float(np.median(errors)), 6),
        "ate_min": round(float(np.min(errors)), 6),
        "ate_max": round(float(np.max(errors)), 6),
        "ate_std": round(float(np.std(errors)), 6),
    }


def write_associations(
    path: Path,
    pairs: list[tuple[float, float]],
    aligned: np.ndarray,
    groundtruth: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        fieldnames = [
            "estimated_timestamp",
            "groundtruth_timestamp",
            "aligned_x",
            "aligned_y",
            "aligned_z",
            "groundtruth_x",
            "groundtruth_y",
            "groundtruth_z",
            "position_error",
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for index, (est_time, gt_time) in enumerate(pairs):
            error = float(np.linalg.norm(aligned[index] - groundtruth[index]))
            writer.writerow(
                {
                    "estimated_timestamp": est_time,
                    "groundtruth_timestamp": gt_time,
                    "aligned_x": aligned[index, 0],
                    "aligned_y": aligned[index, 1],
                    "aligned_z": aligned[index, 2],
                    "groundtruth_x": groundtruth[index, 0],
                    "groundtruth_y": groundtruth[index, 1],
                    "groundtruth_z": groundtruth[index, 2],
                    "position_error": error,
                }
            )


def plot_trajectory(path: Path, aligned: np.ndarray, groundtruth: np.ndarray, title: str) -> None:
    # 先生への説明用に、上から見たXY軌跡を保存します。
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(7, 6))
    plt.plot(groundtruth[:, 0], groundtruth[:, 1], label="ground truth", linewidth=2)
    plt.plot(aligned[:, 0], aligned[:, 1], label="ORB-SLAM3 aligned", linewidth=1.5)
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.title(title)
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectory", type=Path, required=True)
    parser.add_argument("--groundtruth", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sequence", default="")
    parser.add_argument("--max-diff-sec", type=float, default=0.02)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    estimated = read_tum_trajectory(args.trajectory)
    groundtruth = read_euroc_groundtruth(args.groundtruth)
    estimated_points, groundtruth_points, pairs = associate(estimated, groundtruth, args.max_diff_sec)
    if estimated_points.shape[0] < 3:
        raise ValueError(f"Only {estimated_points.shape[0]} associated poses found.")

    aligned, scale, rotation, translation = align_sim3(estimated_points, groundtruth_points)
    metrics = compute_metrics(aligned, groundtruth_points)
    sequence = args.sequence or args.trajectory.parent.name
    row = {
        "sequence": sequence,
        "trajectory": str(args.trajectory),
        "groundtruth": str(args.groundtruth),
        "associations": len(pairs),
        "scale": round(scale, 6),
        **metrics,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    # summaryは数値評価、associationsはどの時刻同士を比較したかの詳細確認用です。
    with (args.output_dir / "ate_summary.csv").open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)
    write_associations(args.output_dir / "ate_associations.csv", pairs, aligned, groundtruth_points)
    np.savetxt(args.output_dir / "sim3_rotation.txt", rotation)
    np.savetxt(args.output_dir / "sim3_translation.txt", translation.reshape(1, 3))
    plot_trajectory(args.output_dir / "trajectory_xy.png", aligned, groundtruth_points, f"{sequence} trajectory")
    print(row)


if __name__ == "__main__":
    main()
