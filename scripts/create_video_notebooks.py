#!/usr/bin/env python3
"""Create one inspection notebook per extracted video sequence."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMES_ROOT = PROJECT_ROOT / "data" / "interim" / "frames_10fps"
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks" / "videos"


def markdown_cell(source: str) -> dict[str, object]:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code_cell(source: str) -> dict[str, object]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def notebook(cells: list[dict[str, object]]) -> dict[str, object]:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "pygments_lexer": "ipython3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def iter_sequences() -> list[str]:
    return [
        metadata_path.parent.relative_to(FRAMES_ROOT).as_posix()
        for metadata_path in sorted(FRAMES_ROOT.rglob("metadata.json"))
    ]


def notebook_name(sequence: str) -> str:
    return f"{sequence.replace('/', '_')}.ipynb"


def make_sequence_notebook(sequence: str) -> dict[str, object]:
    title = sequence.replace("/", " / ")
    cells = [
        markdown_cell(
            f"# {title}\n\n"
            "このノートブックは、1本の動画についてフレーム確認、歪み補正の試行、ORB特徴点検出、"
            "隣接フレームのマッチング、特徴量ファイルの確認を行うための作業場所です。"
        ),
        code_cell(
            "from pathlib import Path\n"
            "import json\n\n"
            "import cv2\n"
            "import numpy as np\n"
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt\n\n"
            "def find_project_root(start: Path) -> Path:\n"
            "    for candidate in [start, *start.parents]:\n"
            "        if (candidate / 'data').exists() and (candidate / 'scripts').exists():\n"
            "            return candidate\n"
            "    raise RuntimeError('Run this notebook from inside the my-research project.')\n\n"
            "PROJECT_ROOT = find_project_root(Path.cwd().resolve())\n"
            f"SEQUENCE = {sequence!r}\n"
            "FRAMES_ROOT = PROJECT_ROOT / 'data' / 'interim' / 'frames_10fps'\n"
            "FEATURES_ROOT = PROJECT_ROOT / 'results' / 'orb_features_n1000'\n"
            "BUDGET_CSV = PROJECT_ROOT / 'results' / 'feature_budgets' / 'summary.csv'\n"
            "CAMERA_CONFIG = PROJECT_ROOT / 'configs' / 'orbslam3' / 'iphone_vertical_1080x1920_approx.yaml'\n\n"
            "sequence_dir = FRAMES_ROOT / SEQUENCE\n"
            "frame_paths = sorted(sequence_dir.glob('frame_*.jpg'))\n"
            "metadata_path = sequence_dir / 'metadata.json'\n"
            "metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}\n\n"
            "print(f'PROJECT_ROOT: {PROJECT_ROOT}')\n"
            "print(f'SEQUENCE: {SEQUENCE}')\n"
            "print(f'frames: {len(frame_paths)}')\n"
            "metadata\n"
        ),
        markdown_cell("## 代表フレーム\n\n動画全体から等間隔にフレームを抜き出して、撮影状況を確認します。"),
        code_cell(
            "if not frame_paths:\n"
            "    raise FileNotFoundError(f'No frames found in {sequence_dir}')\n\n"
            "indices = np.linspace(0, len(frame_paths) - 1, min(6, len(frame_paths)), dtype=int)\n"
            "fig, axes = plt.subplots(1, len(indices), figsize=(3.2 * len(indices), 5))\n"
            "if len(indices) == 1:\n"
            "    axes = [axes]\n"
            "for ax, index in zip(axes, indices):\n"
            "    image = cv2.imread(str(frame_paths[index]))\n"
            "    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)\n"
            "    ax.imshow(image)\n"
            "    ax.set_title(frame_paths[index].stem)\n"
            "    ax.axis('off')\n"
            "plt.tight_layout()\n"
        ),
        markdown_cell(
            "## 特徴点数と通信量の概要\n\n"
            "`scripts/evaluate_feature_budgets.py` の結果から、この動画の特徴点予算ごとの概算を見ます。"
        ),
        code_cell(
            "budget = pd.read_csv(BUDGET_CSV)\n"
            "sequence_budget = budget[budget['sequence'] == SEQUENCE].copy()\n"
            "sequence_budget\n"
        ),
        code_cell(
            "columns = [\n"
            "    'nfeatures',\n"
            "    'avg_keypoints',\n"
            "    'avg_good_matches_to_previous',\n"
            "    'avg_compact_packet_bytes_per_frame',\n"
            "    'avg_jpeg_bytes_per_frame',\n"
            "    'compact_packet_vs_jpeg_ratio',\n"
            "]\n"
            "sequence_budget[columns]\n"
        ),
        markdown_cell(
            "## ORB特徴点の可視化\n\n"
            "`frame_index` と `nfeatures` を変えると、別フレームや別の特徴点数で確認できます。"
        ),
        code_cell(
            "frame_index = 0\n"
            "nfeatures = 1000\n\n"
            "image_bgr = cv2.imread(str(frame_paths[frame_index]))\n"
            "gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)\n"
            "orb = cv2.ORB_create(nfeatures=nfeatures)\n"
            "keypoints, descriptors = orb.detectAndCompute(gray, None)\n"
            "vis = cv2.drawKeypoints(\n"
            "    image_bgr,\n"
            "    keypoints,\n"
            "    None,\n"
            "    color=(0, 255, 0),\n"
            "    flags=cv2.DrawMatchesFlags_DRAW_RICH_KEYPOINTS,\n"
            ")\n\n"
            "plt.figure(figsize=(8, 12))\n"
            "plt.imshow(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))\n"
            "plt.title(f'{frame_paths[frame_index].name}: {len(keypoints)} keypoints')\n"
            "plt.axis('off')\n"
            "plt.show()\n\n"
            "len(keypoints), None if descriptors is None else descriptors.shape\n"
        ),
        markdown_cell(
            "## 歪み補正の試行\n\n"
            "ここでは処理の流れを確認するため、仮の内部パラメータとゼロ歪み係数を使っています。"
            "正確な歪み補正には、チェッカーボード等で実測したカメラキャリブレーション結果に置き換えてください。"
        ),
        code_cell(
            "height, width = image_bgr.shape[:2]\n"
            "camera_matrix = np.array(\n"
            "    [[1500.0, 0.0, width / 2], [0.0, 1500.0, height / 2], [0.0, 0.0, 1.0]],\n"
            "    dtype=np.float32,\n"
            ")\n"
            "dist_coeffs = np.zeros(5, dtype=np.float32)\n"
            "undistorted = cv2.undistort(image_bgr, camera_matrix, dist_coeffs)\n\n"
            "fig, axes = plt.subplots(1, 2, figsize=(10, 8))\n"
            "axes[0].imshow(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))\n"
            "axes[0].set_title('original')\n"
            "axes[0].axis('off')\n"
            "axes[1].imshow(cv2.cvtColor(undistorted, cv2.COLOR_BGR2RGB))\n"
            "axes[1].set_title('undistorted trial')\n"
            "axes[1].axis('off')\n"
            "plt.tight_layout()\n"
        ),
        markdown_cell(
            "## 隣接フレームのマッチング\n\n"
            "隣り合う2フレーム間でORB特徴量を対応付け、追跡しやすい映像かを確認します。"
        ),
        code_cell(
            "i = 0\n"
            "j = min(i + 1, len(frame_paths) - 1)\n"
            "img1_gray = cv2.imread(str(frame_paths[i]), cv2.IMREAD_GRAYSCALE)\n"
            "img2_gray = cv2.imread(str(frame_paths[j]), cv2.IMREAD_GRAYSCALE)\n\n"
            "kp1, des1 = orb.detectAndCompute(img1_gray, None)\n"
            "kp2, des2 = orb.detectAndCompute(img2_gray, None)\n"
            "matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)\n"
            "matches = [] if des1 is None or des2 is None else matcher.match(des1, des2)\n"
            "matches = sorted(matches, key=lambda match: match.distance)\n"
            "good_matches = [match for match in matches if match.distance <= 64]\n\n"
            "drawn = cv2.drawMatches(\n"
            "    img1_gray,\n"
            "    kp1,\n"
            "    img2_gray,\n"
            "    kp2,\n"
            "    matches[:80],\n"
            "    None,\n"
            "    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,\n"
            ")\n"
            "plt.figure(figsize=(14, 8))\n"
            "plt.imshow(drawn, cmap='gray')\n"
            "plt.title(f'{frame_paths[i].name} -> {frame_paths[j].name}: {len(matches)} matches, {len(good_matches)} good')\n"
            "plt.axis('off')\n"
            "plt.show()\n\n"
            "len(kp1), len(kp2), len(matches), len(good_matches)\n"
        ),
        markdown_cell(
            "## 保存済み特徴量ファイルの確認\n\n"
            "`scripts/export_orb_features.py` で作った `.npz` を読み込み、送信対象になる特徴点と記述子を確認します。"
        ),
        code_cell(
            "feature_file = FEATURES_ROOT / SEQUENCE / f'{frame_paths[frame_index].stem}.npz'\n"
            "with np.load(feature_file) as feature_data:\n"
            "    saved_keypoints = feature_data['keypoints']\n"
            "    saved_descriptors = feature_data['descriptors']\n\n"
            "feature_file, saved_keypoints.shape, saved_descriptors.shape, saved_descriptors.dtype\n"
        ),
        markdown_cell(
            "## Essential Matrixの最小確認\n\n"
            "仮のカメラ内部パラメータなので、ここでの値は精度評価ではなく、処理パイプラインの確認用です。"
        ),
        code_cell(
            "if len(matches) >= 8:\n"
            "    pts1 = np.float32([kp1[match.queryIdx].pt for match in matches])\n"
            "    pts2 = np.float32([kp2[match.trainIdx].pt for match in matches])\n"
            "    essential_matrix, inlier_mask = cv2.findEssentialMat(\n"
            "        pts1,\n"
            "        pts2,\n"
            "        camera_matrix,\n"
            "        method=cv2.RANSAC,\n"
            "        prob=0.999,\n"
            "        threshold=1.0,\n"
            "    )\n"
            "    inliers = int(inlier_mask.sum()) if inlier_mask is not None else 0\n"
            "else:\n"
            "    essential_matrix = None\n"
            "    inliers = 0\n\n"
            "inliers, None if essential_matrix is None else essential_matrix.shape\n"
        ),
    ]
    return notebook(cells)


def make_index_notebook(sequences: list[str]) -> dict[str, object]:
    rows = "\n".join(
        f"- [{sequence}]({notebook_name(sequence)})" for sequence in sequences
    )
    cells = [
        markdown_cell(
            "# Video notebooks\n\n"
            "各動画ごとの確認用ノートブックです。まず対象動画を開き、上から順に実行してください。\n\n"
            f"{rows}\n"
        ),
        code_cell(
            "from pathlib import Path\n"
            "import json\n"
            "import pandas as pd\n\n"
            "def find_project_root(start: Path) -> Path:\n"
            "    for candidate in [start, *start.parents]:\n"
            "        if (candidate / 'data').exists() and (candidate / 'scripts').exists():\n"
            "            return candidate\n"
            "    raise RuntimeError('Run this notebook from inside the my-research project.')\n\n"
            "project_root = find_project_root(Path.cwd().resolve())\n"
            "frames_root = project_root / 'data' / 'interim' / 'frames_10fps'\n"
            "rows = []\n"
            "for metadata_path in sorted(frames_root.rglob('metadata.json')):\n"
            "    metadata = json.loads(metadata_path.read_text())\n"
            "    sequence = metadata_path.parent.relative_to(frames_root).as_posix()\n"
            "    rows.append({\n"
            "        'sequence': sequence,\n"
            "        'frames': metadata.get('frames_written'),\n"
            "        'duration_sec': metadata.get('source_duration_sec'),\n"
            "        'source_fps': metadata.get('source_fps'),\n"
            "        'target_fps': metadata.get('target_fps'),\n"
            "        'size': f\"{metadata.get('source_width')}x{metadata.get('source_height')}\",\n"
            "    })\n"
            "pd.DataFrame(rows)\n"
        ),
    ]
    return notebook(cells)


def write_notebook(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    sequences = iter_sequences()
    if not sequences:
        raise SystemExit(f"No metadata.json files found under {FRAMES_ROOT}")

    write_notebook(NOTEBOOK_DIR / "00_video_index.ipynb", make_index_notebook(sequences))
    for sequence in sequences:
        write_notebook(NOTEBOOK_DIR / notebook_name(sequence), make_sequence_notebook(sequence))

    print(f"Wrote {len(sequences) + 1} notebooks to {NOTEBOOK_DIR}")


if __name__ == "__main__":
    main()
