#!/usr/bin/env python3
"""Extract timestamped frames from research videos."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

import cv2
from tqdm import tqdm


VIDEO_EXTENSIONS = {".avi", ".mkv", ".mov", ".mp4"}


def iter_videos(input_root: Path):
    ignored_parts = {"interim", "processed", "sample"}
    for path in sorted(input_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        if any(part in ignored_parts for part in path.relative_to(input_root).parts):
            continue
        yield path


def output_dir_for(video_path: Path, input_root: Path, output_root: Path) -> Path:
    relative = video_path.relative_to(input_root)
    return output_root / relative.parent / video_path.stem


def prepare_sequence_dir(sequence_dir: Path, overwrite: bool) -> bool:
    if not sequence_dir.exists():
        sequence_dir.mkdir(parents=True, exist_ok=True)
        return True

    existing_frames = list(sequence_dir.glob("frame_*.jpg"))
    existing_metadata = [sequence_dir / "frames.csv", sequence_dir / "metadata.json"]
    existing_metadata = [path for path in existing_metadata if path.exists()]
    if not existing_frames and not existing_metadata:
        return True

    if not overwrite:
        return False

    shutil.rmtree(sequence_dir)
    sequence_dir.mkdir(parents=True, exist_ok=True)
    return True


def extract_video(
    video_path: Path,
    input_root: Path,
    output_root: Path,
    target_fps: float,
    overwrite: bool,
) -> dict[str, object]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {
            "video": str(video_path.relative_to(input_root)),
            "status": "failed_open",
            "frames_written": 0,
        }

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / source_fps if source_fps > 0 else 0.0
    interval_sec = 1.0 / target_fps
    next_emit_sec = 0.0
    frames_written = 0
    rows: list[dict[str, object]] = []

    sequence_dir = output_dir_for(video_path, input_root, output_root)
    if not prepare_sequence_dir(sequence_dir, overwrite):
        cap.release()
        return {
            "video": str(video_path.relative_to(input_root)),
            "status": "skipped_existing_output",
            "frames_written": 0,
        }

    with tqdm(total=total_frames, desc=video_path.name, unit="frame") as progress:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            source_frame_index = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            timestamp_sec = source_frame_index / source_fps if source_fps > 0 else 0.0

            if timestamp_sec + 1e-9 >= next_emit_sec:
                output_name = f"frame_{frames_written:06d}.jpg"
                output_path = sequence_dir / output_name
                cv2.imwrite(str(output_path), frame)
                rows.append(
                    {
                        "frame_file": output_name,
                        "source_frame_index": source_frame_index,
                        "timestamp_sec": round(timestamp_sec, 6),
                    }
                )
                frames_written += 1
                next_emit_sec += interval_sec

            progress.update(1)

    cap.release()

    metadata = {
        "video": str(video_path.relative_to(input_root)),
        "status": "ok",
        "target_fps": target_fps,
        "source_fps": round(source_fps, 6),
        "source_frames": total_frames,
        "source_width": width,
        "source_height": height,
        "source_duration_sec": round(duration_sec, 6),
        "frames_written": frames_written,
    }

    with (sequence_dir / "metadata.json").open("w", encoding="utf-8") as json_file:
        json.dump(metadata, json_file, indent=2, ensure_ascii=False)

    with (sequence_dir / "frames.csv").open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["frame_file", "source_frame_index", "timestamp_sec"])
        writer.writeheader()
        writer.writerows(rows)

    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("data"))
    parser.add_argument("--output-root", type=Path, default=Path("data/interim/frames"))
    parser.add_argument("--fps", type=float, default=2.0)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing extracted frames for each video.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.fps <= 0:
        raise ValueError("--fps must be greater than zero")

    videos = list(iter_videos(args.input_root))
    summaries = [
        extract_video(video, args.input_root, args.output_root, args.fps, args.overwrite)
        for video in videos
    ]

    args.output_root.mkdir(parents=True, exist_ok=True)
    with (args.output_root / "summary.json").open("w", encoding="utf-8") as json_file:
        json.dump(summaries, json_file, indent=2, ensure_ascii=False)

    ok_count = sum(1 for item in summaries if item.get("status") == "ok")
    print(f"Extracted frames for {ok_count}/{len(summaries)} videos into {args.output_root}")


if __name__ == "__main__":
    main()
