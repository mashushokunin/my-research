#!/usr/bin/env python3
"""キーフレームごとの共有データ量を画像から見積もります。

ORB-SLAM3のKeyFrameTrajectoryに出た時刻を使い、対応するEuRoC画像からORB特徴量を
再抽出します。これはORB-SLAM3内部値の厳密な取得ではなく、通信量比較のための
近似評価です。
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from statistics import mean

import cv2


ORB_DESCRIPTOR_BYTES = 32
COMPACT_KEYPOINT_BYTES = 9
FLOAT_KEYPOINT_BYTES = 24
# poseは tx, ty, tz, qx, qy, qz, qw の7値として通信する想定です。
POSE_FLOAT32_BYTES = 7 * 4
POSE_FLOAT64_BYTES = 7 * 8


def normalize_timestamp(value: float) -> float:
    # EuRoCのナノ秒時刻とORB-SLAM3軌跡の秒時刻を同じ単位にそろえます。
    return value * 1e-9 if value > 1e12 else value


def read_trajectory_timestamps(path: Path) -> list[float]:
    # KeyFrameTrajectory.txt の各行から、キーフレーム時刻だけを取り出します。
    timestamps: list[float] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts:
            timestamps.append(normalize_timestamp(float(parts[0])))
    return timestamps


def read_euroc_images(sequence_dir: Path) -> dict[float, Path]:
    # EuRoCの cam0/data.csv を読み、各画像ファイルを時刻で引けるようにします。
    csv_path = sequence_dir / "mav0/cam0/data.csv"
    image_dir = sequence_dir / "mav0/cam0/data"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing EuRoC camera CSV: {csv_path}")

    images: dict[float, Path] = {}
    with csv_path.open(newline="", encoding="utf-8", errors="replace") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if not row or row[0].startswith("#"):
                continue
            timestamp = normalize_timestamp(float(row[0]))
            filename = row[1] if len(row) > 1 else f"{row[0]}.png"
            image_path = image_dir / filename
            if image_path.exists():
                images[timestamp] = image_path
    return images


def nearest_image(timestamp: float, images: dict[float, Path], max_diff_sec: float) -> tuple[float, Path] | None:
    # キーフレーム時刻に最も近い画像を探します。差が大きい場合は誤対応として捨てます。
    times = sorted(images.keys())
    if not times:
        return None
    lo = 0
    hi = len(times)
    while lo < hi:
        mid = (lo + hi) // 2
        if times[mid] < timestamp:
            lo = mid + 1
        else:
            hi = mid
    candidates = []
    if lo < len(times):
        candidates.append(times[lo])
    if lo > 0:
        candidates.append(times[lo - 1])
    if not candidates:
        return None
    best = min(candidates, key=lambda value: abs(value - timestamp))
    if abs(best - timestamp) > max_diff_sec:
        return None
    return best, images[best]


def parse_nfeatures(settings: Path, default: int) -> int:
    # ORB-SLAM3設定と同じ特徴点数で再抽出し、内部処理に近い見積もりにします。
    if not settings.exists():
        return default
    text = settings.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"ORBextractor\.nFeatures:\s*([0-9]+)", text)
    return int(match.group(1)) if match else default


def safe_mean(values: list[float]) -> float:
    return round(mean(values), 3) if values else 0.0


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    # 先生への説明では、キーフレームごとの詳細より平均値の方が使いやすいため要約します。
    if not rows:
        return []
    numeric_columns = [
        "image_bytes",
        "keypoints",
        "descriptor_rows",
        "descriptor_cols",
        "descriptor_bytes",
        "compact_feature_packet_bytes",
        "float_feature_packet_bytes",
        "pose_float32_bytes",
        "pose_float64_bytes",
        "compact_packet_vs_image_ratio",
        "float_packet_vs_image_ratio",
    ]
    summary = {"keyframes": len(rows)}
    for column in numeric_columns:
        summary[f"avg_{column}"] = safe_mean([float(row[column]) for row in rows])
    return [summary]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trajectory", type=Path, required=True)
    parser.add_argument("--sequence-dir", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=Path("configs/orbslam3/iphone_vertical_1080x1920_approx.yaml"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-diff-sec", type=float, default=0.02)
    parser.add_argument("--nfeatures", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    nfeatures = args.nfeatures or parse_nfeatures(args.settings, 1000)
    orb = cv2.ORB_create(nfeatures=nfeatures)
    timestamps = read_trajectory_timestamps(args.trajectory)
    images = read_euroc_images(args.sequence_dir)

    rows: list[dict[str, object]] = []
    for keyframe_index, timestamp in enumerate(timestamps):
        match = nearest_image(timestamp, images, args.max_diff_sec)
        if match is None:
            continue
        image_timestamp, image_path = match
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        keypoints, descriptors = orb.detectAndCompute(image, None)
        descriptor_rows = 0 if descriptors is None else int(descriptors.shape[0])
        descriptor_cols = 0 if descriptors is None else int(descriptors.shape[1])
        descriptor_bytes = 0 if descriptors is None else int(descriptors.nbytes)
        keypoint_count = len(keypoints)
        # compactは量子化keypoint + descriptor、floatは素直なfloat表現という2通りで概算します。
        compact_packet = keypoint_count * (ORB_DESCRIPTOR_BYTES + COMPACT_KEYPOINT_BYTES) + POSE_FLOAT32_BYTES
        float_packet = keypoint_count * (ORB_DESCRIPTOR_BYTES + FLOAT_KEYPOINT_BYTES) + POSE_FLOAT64_BYTES
        image_bytes = image_path.stat().st_size
        height, width = image.shape[:2]

        rows.append(
            {
                "keyframe_index": keyframe_index,
                "trajectory_timestamp": timestamp,
                "image_timestamp": image_timestamp,
                "image_file": str(image_path.relative_to(args.sequence_dir)),
                "image_width": width,
                "image_height": height,
                "image_bytes": image_bytes,
                "keypoints": keypoint_count,
                "descriptor_rows": descriptor_rows,
                "descriptor_cols": descriptor_cols,
                "descriptor_bytes": descriptor_bytes,
                "compact_feature_packet_bytes": compact_packet,
                "float_feature_packet_bytes": float_packet,
                "pose_float32_bytes": POSE_FLOAT32_BYTES,
                "pose_float64_bytes": POSE_FLOAT64_BYTES,
                "compact_packet_vs_image_ratio": round(compact_packet / image_bytes, 6) if image_bytes else 0.0,
                "float_packet_vs_image_ratio": round(float_packet / image_bytes, 6) if image_bytes else 0.0,
            }
        )

    write_csv(args.output_dir / "keyframe_payload.csv", rows)
    write_csv(args.output_dir / "summary.csv", summarize(rows))
    print(f"Wrote {len(rows)} keyframe payload rows to {args.output_dir}")


if __name__ == "__main__":
    main()
