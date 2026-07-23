#!/usr/bin/env python3
"""Export ORB keypoints and descriptors for each extracted frame."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2
import numpy as np
from tqdm import tqdm


ORB_DESCRIPTOR_BYTES = 32
# 通信パケットサイズを見積もるためのkeypoint情報サイズです。
COMPACT_KEYPOINT_BYTES = 9
FLOAT_KEYPOINT_BYTES = 24


def iter_sequences(frames_root: Path):
    for metadata_path in sorted(frames_root.rglob("metadata.json")):
        yield metadata_path.parent


def sequence_name(sequence_dir: Path, frames_root: Path) -> str:
    return sequence_dir.relative_to(frames_root).as_posix()


def keypoints_to_array(keypoints: tuple[cv2.KeyPoint, ...]) -> np.ndarray:
    # cv2.KeyPoint はそのままだとnp.savezで扱いにくいので、数値配列に変換します。
    # 列は x, y, size, angle, response, octave, class_id です。
    rows = [
        [
            keypoint.pt[0],
            keypoint.pt[1],
            keypoint.size,
            keypoint.angle,
            keypoint.response,
            keypoint.octave,
            keypoint.class_id,
        ]
        for keypoint in keypoints
    ]
    return np.asarray(rows, dtype=np.float32).reshape((-1, 7))


def export_sequence(
    sequence_dir: Path,
    frames_root: Path,
    output_root: Path,
    orb: cv2.ORB,
    overwrite: bool,
) -> list[dict[str, object]]:
    # 1シーケンス分のORB特徴点とdescriptorを、フレームごとの .npz に保存します。
    sequence = sequence_name(sequence_dir, frames_root)
    output_sequence_dir = output_root / sequence
    output_sequence_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for frame_path in tqdm(sorted(sequence_dir.glob("frame_*.jpg")), desc=sequence, unit="frame"):
        output_path = output_sequence_dir / f"{frame_path.stem}.npz"
        if output_path.exists() and not overwrite:
            # 既存の特徴量ファイルがあれば再利用し、manifestだけ作り直せるようにします。
            npz_size = output_path.stat().st_size
            with np.load(output_path) as existing:
                keypoint_count = int(existing["keypoints"].shape[0])
        else:
            # 特徴点抽出はグレースケール画像で行います。
            image = cv2.imread(str(frame_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                keypoints = []
                descriptors = np.empty((0, ORB_DESCRIPTOR_BYTES), dtype=np.uint8)
            else:
                keypoints, descriptors = orb.detectAndCompute(image, None)
                if descriptors is None:
                    descriptors = np.empty((0, ORB_DESCRIPTOR_BYTES), dtype=np.uint8)

            keypoint_array = keypoints_to_array(tuple(keypoints))
            # keypoints と descriptors を1フレーム単位で保存します。
            # 今後、画像ではなく特徴量だけを送る実験の入力になります。
            np.savez_compressed(
                output_path,
                keypoints=keypoint_array,
                descriptors=descriptors,
            )
            keypoint_count = int(keypoint_array.shape[0])
            npz_size = output_path.stat().st_size

        rows.append(
            {
                # manifest.csv は、各フレームの特徴量ファイルと通信量概算を対応づける一覧です。
                "sequence": sequence,
                "frame_file": frame_path.name,
                "feature_file": str(output_path.relative_to(output_root)),
                "keypoints": keypoint_count,
                "descriptor_bytes": keypoint_count * ORB_DESCRIPTOR_BYTES,
                "compact_packet_bytes": keypoint_count * (ORB_DESCRIPTOR_BYTES + COMPACT_KEYPOINT_BYTES),
                "float_packet_bytes": keypoint_count * (ORB_DESCRIPTOR_BYTES + FLOAT_KEYPOINT_BYTES),
                "npz_bytes": npz_size,
            }
        )

    return rows


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "sequence",
        "frame_file",
        "feature_file",
        "keypoints",
        "descriptor_bytes",
        "compact_packet_bytes",
        "float_packet_bytes",
        "npz_bytes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-root", type=Path, default=Path("data/interim/frames_10fps"))
    parser.add_argument("--output-root", type=Path, default=Path("results/orb_features_n1000"))
    parser.add_argument("--nfeatures", type=int, default=1000)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    orb = cv2.ORB_create(nfeatures=args.nfeatures)
    rows: list[dict[str, object]] = []

    for sequence_dir in iter_sequences(args.frames_root):
        rows.extend(export_sequence(sequence_dir, args.frames_root, args.output_root, orb, args.overwrite))

    write_manifest(args.output_root / "manifest.csv", rows)
    print(f"Wrote {len(rows)} feature files to {args.output_root}")


if __name__ == "__main__":
    main()
