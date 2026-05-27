#!/usr/bin/env python3
"""Run ORB-SLAM3 mono_tum on prepared TUM-style sequences."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def iter_sequences(sequence_root: Path):
    for rgb_txt in sorted(sequence_root.rglob("rgb.txt")):
        yield rgb_txt.parent


def result_name(sequence_dir: Path, sequence_root: Path) -> str:
    return "_".join(sequence_dir.relative_to(sequence_root).parts)


def build_env(orbslam_root: Path, pangolin_build: Path) -> dict[str, str]:
    env = os.environ.copy()
    library_paths = [
        orbslam_root / "lib",
        orbslam_root / "Thirdparty/DBoW2/lib",
        orbslam_root / "Thirdparty/g2o/lib",
        pangolin_build,
    ]
    existing = env.get("DYLD_LIBRARY_PATH")
    values = [str(path) for path in library_paths]
    if existing:
        values.append(existing)
    env["DYLD_LIBRARY_PATH"] = ":".join(values)
    return env


def run_sequence(
    sequence_dir: Path,
    sequence_root: Path,
    output_root: Path,
    binary: Path,
    vocabulary: Path,
    settings: Path,
    env: dict[str, str],
    overwrite: bool,
) -> dict[str, object]:
    output_dir = output_root / result_name(sequence_dir, sequence_root)
    trajectory = output_dir / "KeyFrameTrajectory.txt"
    if trajectory.exists() and not overwrite:
        return {
            "sequence": str(sequence_dir.relative_to(sequence_root)),
            "status": "skipped_existing",
            "returncode": 0,
        }

    if output_dir.exists() and overwrite:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [str(binary), str(vocabulary), str(settings), str(sequence_dir)]
    log_path = output_dir / "run.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write("$ " + " ".join(command) + "\n\n")
        log_file.flush()
        process = subprocess.run(
            command,
            cwd=output_dir,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    return {
        "sequence": str(sequence_dir.relative_to(sequence_root)),
        "status": "ok" if process.returncode == 0 else "failed",
        "returncode": process.returncode,
        "trajectory_exists": trajectory.exists(),
        "output_dir": str(output_dir),
    }


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = repo_root.parent
    orbslam_root = workspace_root / "external-repos/ORB_SLAM3"

    parser = argparse.ArgumentParser()
    parser.add_argument("--sequence-root", type=Path, default=repo_root / "data/interim/orbslam_tum_10fps")
    parser.add_argument("--output-root", type=Path, default=repo_root / "results/orbslam3_monocular")
    parser.add_argument("--orbslam-root", type=Path, default=orbslam_root)
    parser.add_argument("--pangolin-build", type=Path, default=workspace_root / "external-repos/Pangolin/build")
    parser.add_argument("--settings", type=Path, default=repo_root / "configs/orbslam3/iphone_vertical_1080x1920_approx.yaml")
    parser.add_argument(
        "--only",
        help="Run one sequence relative to --sequence-root, e.g. structured/IMG_5978.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    binary = args.orbslam_root / "Examples/Monocular/mono_tum"
    vocabulary = args.orbslam_root / "Vocabulary/ORBvoc.txt"
    env = build_env(args.orbslam_root, args.pangolin_build)

    required_paths = [binary, vocabulary, args.settings, args.sequence_root]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required paths: " + ", ".join(str(path) for path in missing))

    summaries = []
    sequence_dirs = list(iter_sequences(args.sequence_root))
    if args.only:
        sequence_dirs = [
            sequence_dir
            for sequence_dir in sequence_dirs
            if sequence_dir.relative_to(args.sequence_root).as_posix() == args.only
        ]
        if not sequence_dirs:
            raise ValueError(f"No sequence matched --only {args.only}")

    for sequence_dir in sequence_dirs:
        summary = run_sequence(
            sequence_dir,
            args.sequence_root,
            args.output_root,
            binary,
            vocabulary,
            args.settings,
            env,
            args.overwrite,
        )
        summaries.append(summary)
        print(summary)

    ok_count = sum(1 for item in summaries if item["status"] in {"ok", "skipped_existing"})
    print(f"Finished {ok_count}/{len(summaries)} sequences")


if __name__ == "__main__":
    main()
