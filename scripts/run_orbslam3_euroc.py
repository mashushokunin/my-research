#!/usr/bin/env python3
"""EuRoC公開データセットでORB-SLAM3 monocularを実行します。

Jetson実機へ進む前に、公開データセットで単体SLAMを安定して動かすための
最小実験基盤です。実行ログ、軌跡、実行時間を保存し、ATE評価へつなげます。
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


SEQUENCE_ALIASES = {
    "MH_01_easy": "MH01",
    "MH_02_easy": "MH02",
    "MH_03_medium": "MH03",
    "MH_04_difficult": "MH04",
    "MH_05_difficult": "MH05",
    "V1_01_easy": "V101",
    "V1_02_medium": "V102",
    "V1_03_difficult": "V103",
    "V2_01_easy": "V201",
    "V2_02_medium": "V202",
    "V2_03_difficult": "V203",
}


def build_env(orbslam_root: Path, pangolin_build: Path) -> dict[str, str]:
    # ORB-SLAM3の実行時に必要な共有ライブラリを見つけられるようにします。
    # macOS/Linuxの両方を想定して DYLD_LIBRARY_PATH と LD_LIBRARY_PATH を設定します。
    env = os.environ.copy()
    library_paths = [
        orbslam_root / "lib",
        orbslam_root / "Thirdparty/DBoW2/lib",
        orbslam_root / "Thirdparty/g2o/lib",
        pangolin_build,
    ]
    values = [str(path) for path in library_paths]
    for variable in ["DYLD_LIBRARY_PATH", "LD_LIBRARY_PATH"]:
        existing = env.get(variable)
        env[variable] = ":".join([*values, existing] if existing else values)
    return env


def sequence_alias(sequence: str) -> str:
    return SEQUENCE_ALIASES.get(sequence, sequence)


def resolve_sequence_dir(dataset_root: Path, sequence: str, sequence_dir: Path | None) -> Path:
    # EuRoCは `MH_01_easy` のような正式名でも、`MH01` のような短縮名でも探せるようにします。
    if sequence_dir is not None:
        return sequence_dir.expanduser().resolve()

    candidates = [
        dataset_root / sequence,
        dataset_root / sequence_alias(sequence),
    ]
    for candidate in candidates:
        if (candidate / "mav0").exists():
            return candidate.resolve()

    raise FileNotFoundError(
        "No EuRoC sequence directory found. Tried: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def resolve_timestamps(orbslam_root: Path, sequence: str, timestamps: Path | None) -> Path:
    # ORB-SLAM3公式サンプルに含まれるタイムスタンプファイルを利用します。
    if timestamps is not None:
        return timestamps.expanduser().resolve()

    alias = sequence_alias(sequence)
    candidates = [
        orbslam_root / "Examples/Monocular/EuRoC_TimeStamps" / f"{alias}.txt",
        orbslam_root / "Examples/Stereo/EuRoC_TimeStamps" / f"{alias}.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        "No ORB-SLAM3 EuRoC timestamp file found. Tried: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def copy_if_exists(source: Path, destination: Path) -> None:
    if source.exists() and source.resolve() != destination.resolve():
        shutil.copy2(source, destination)


def normalize_outputs(output_dir: Path, run_name: str) -> dict[str, object]:
    # ORB-SLAM3は run_name 付きの軌跡名で出すことがあるため、後続処理用に標準名へコピーします。
    trajectory_candidates = sorted(output_dir.glob("KeyFrameTrajectory*.txt"))
    camera_candidates = sorted(output_dir.glob("CameraTrajectory*.txt"))
    if trajectory_candidates:
        copy_if_exists(trajectory_candidates[0], output_dir / "KeyFrameTrajectory.txt")
    if camera_candidates:
        copy_if_exists(camera_candidates[0], output_dir / "CameraTrajectory.txt")

    return {
        "run_name": run_name,
        "keyframe_trajectory": str(output_dir / "KeyFrameTrajectory.txt"),
        "keyframe_trajectory_exists": (output_dir / "KeyFrameTrajectory.txt").exists(),
        "camera_trajectory": str(output_dir / "CameraTrajectory.txt"),
        "camera_trajectory_exists": (output_dir / "CameraTrajectory.txt").exists(),
        "raw_keyframe_outputs": [path.name for path in trajectory_candidates],
        "raw_camera_outputs": [path.name for path in camera_candidates],
    }


def run_sequence(
    sequence: str,
    sequence_dir: Path,
    output_root: Path,
    binary: Path,
    vocabulary: Path,
    settings: Path,
    timestamps: Path,
    env: dict[str, str],
    overwrite: bool,
) -> dict[str, object]:
    output_dir = output_root / sequence
    if output_dir.exists() and overwrite:
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    trajectory = output_dir / "KeyFrameTrajectory.txt"
    if trajectory.exists() and not overwrite:
        # 既に軌跡がある場合は再実行せず、結果の存在確認だけ返します。
        return {
            "sequence": sequence,
            "status": "skipped_existing",
            "returncode": 0,
            "output_dir": str(output_dir),
            **normalize_outputs(output_dir, sequence),
        }

    run_name = f"dataset-{sequence_alias(sequence)}_mono"
    # mono_euroc の引数順は ORB-SLAM3公式サンプルに合わせています。
    command = [
        str(binary),
        str(vocabulary),
        str(settings),
        str(sequence_dir),
        str(timestamps),
        run_name,
    ]
    log_path = output_dir / "run.log"
    started_at = time.perf_counter()
    with log_path.open("w", encoding="utf-8") as log_file:
        # 標準出力と標準エラーを同じログへ保存し、停止原因をあとから追えるようにします。
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
    elapsed_sec = time.perf_counter() - started_at

    outputs = normalize_outputs(output_dir, run_name)
    metadata = {
        "sequence": sequence,
        "sequence_dir": str(sequence_dir),
        "settings": str(settings),
        "timestamps": str(timestamps),
        "status": "ok" if process.returncode == 0 else "failed",
        "returncode": process.returncode,
        "elapsed_sec": round(elapsed_sec, 3),
        "output_dir": str(output_dir),
        "log_path": str(log_path),
        **outputs,
    }
    # run_summary.json は、実行条件と出力ファイルの有無をあとから確認するための記録です。
    with (output_dir / "run_summary.json").open("w", encoding="utf-8") as json_file:
        json.dump(metadata, json_file, indent=2, ensure_ascii=False)
    return metadata


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "sequence",
        "status",
        "returncode",
        "elapsed_sec",
        "keyframe_trajectory_exists",
        "camera_trajectory_exists",
        "output_dir",
        "log_path",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = repo_root.parent
    orbslam_root = workspace_root / "external-repos/ORB_SLAM3"

    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=repo_root / "data/euroc")
    parser.add_argument("--sequence", action="append")
    parser.add_argument("--sequence-dir", type=Path, help="Run one explicit EuRoC sequence directory.")
    parser.add_argument("--output-root", type=Path, default=repo_root / "results/orbslam3_euroc")
    parser.add_argument("--orbslam-root", type=Path, default=orbslam_root)
    parser.add_argument("--pangolin-build", type=Path, default=workspace_root / "external-repos/Pangolin/build")
    parser.add_argument("--settings", type=Path, default=orbslam_root / "Examples/Monocular/EuRoC.yaml")
    parser.add_argument("--timestamps", type=Path, help="ORB-SLAM3 EuRoC timestamp file for --sequence-dir.")
    parser.add_argument("--binary", type=Path, default=orbslam_root / "Examples/Monocular/mono_euroc")
    parser.add_argument("--vocabulary", type=Path, default=orbslam_root / "Vocabulary/ORBvoc.txt")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    required_paths = [args.binary, args.vocabulary, args.settings, args.orbslam_root]
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        # データセット以外の必須ファイルがない場合は、実行前に分かるようにします。
        raise FileNotFoundError("Missing required paths: " + ", ".join(str(path) for path in missing))

    env = build_env(args.orbslam_root, args.pangolin_build)
    rows: list[dict[str, object]] = []
    requested_sequences = args.sequence or ["MH_01_easy"]
    sequences = requested_sequences if args.sequence_dir is None else [requested_sequences[0]]

    for sequence in sequences:
        # 1シーケンスずつ実行し、最後に全体 summary.csv へまとめます。
        sequence_dir = resolve_sequence_dir(args.dataset_root, sequence, args.sequence_dir)
        timestamps = resolve_timestamps(args.orbslam_root, sequence, args.timestamps)
        summary = run_sequence(
            sequence,
            sequence_dir,
            args.output_root,
            args.binary,
            args.vocabulary,
            args.settings,
            timestamps,
            env,
            args.overwrite,
        )
        rows.append(summary)
        print(summary)

    write_summary(args.output_root / "summary.csv", rows)
    ok_count = sum(1 for row in rows if row["status"] in {"ok", "skipped_existing"})
    print(f"Finished {ok_count}/{len(rows)} EuRoC runs")


if __name__ == "__main__":
    main()
