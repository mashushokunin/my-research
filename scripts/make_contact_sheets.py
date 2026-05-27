#!/usr/bin/env python3
"""Create contact sheets for quick visual review of extracted frames."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import cv2
import numpy as np


def iter_sequences(frames_root: Path):
    for metadata_path in sorted(frames_root.rglob("metadata.json")):
        yield metadata_path.parent


def sample_frames(frame_paths: list[Path], max_frames: int) -> list[Path]:
    if len(frame_paths) <= max_frames:
        return frame_paths

    indexes = np.linspace(0, len(frame_paths) - 1, max_frames)
    return [frame_paths[int(round(index))] for index in indexes]


def resize_with_label(image_path: Path, tile_width: int) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read {image_path}")

    height, width = image.shape[:2]
    tile_height = int(height * (tile_width / width))
    resized = cv2.resize(image, (tile_width, tile_height))

    label_height = 32
    labeled = np.full((tile_height + label_height, tile_width, 3), 255, dtype=np.uint8)
    labeled[:tile_height, :] = resized
    cv2.putText(
        labeled,
        image_path.name,
        (8, tile_height + 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 0),
        1,
        cv2.LINE_AA,
    )
    return labeled


def make_contact_sheet(
    sequence_dir: Path,
    frames_root: Path,
    output_root: Path,
    max_frames: int,
    columns: int,
    tile_width: int,
) -> Path | None:
    frame_paths = sorted(sequence_dir.glob("frame_*.jpg"))
    if not frame_paths:
        return None

    sampled = sample_frames(frame_paths, max_frames)
    tiles = [resize_with_label(path, tile_width) for path in sampled]
    tile_height = max(tile.shape[0] for tile in tiles)
    rows = math.ceil(len(tiles) / columns)

    sheet = np.full((rows * tile_height, columns * tile_width, 3), 245, dtype=np.uint8)
    for index, tile in enumerate(tiles):
        row = index // columns
        column = index % columns
        y = row * tile_height
        x = column * tile_width
        sheet[y : y + tile.shape[0], x : x + tile_width] = tile

    relative = sequence_dir.relative_to(frames_root)
    output_path = output_root / relative.with_suffix(".jpg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), sheet)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-root", type=Path, default=Path("data/interim/frames"))
    parser.add_argument("--output-root", type=Path, default=Path("results/contact_sheets"))
    parser.add_argument("--max-frames", type=int, default=12)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--tile-width", type=int, default=240)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_paths = []
    for sequence_dir in iter_sequences(args.frames_root):
        output_path = make_contact_sheet(
            sequence_dir,
            args.frames_root,
            args.output_root,
            args.max_frames,
            args.columns,
            args.tile_width,
        )
        if output_path is not None:
            output_paths.append(output_path)

    print(f"Wrote {len(output_paths)} contact sheets to {args.output_root}")


if __name__ == "__main__":
    main()
