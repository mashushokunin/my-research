#!/usr/bin/env python3
"""Create one inspection notebook per extracted video sequence."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRAMES_ROOT = PROJECT_ROOT / "data" / "interim" / "frames_10fps"
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks" / "videos"


def markdown_cell(source: str) -> dict[str, object]:
    # nbformatの最小構造に合わせてMarkdownセルを作ります。
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def code_cell(source: str) -> dict[str, object]:
    # 実行結果は持たない状態でコードセルを作ります。生成後にNotebook上で実行します。
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
    # frames_10fps以下のmetadata.jsonを起点に、動画ごとのNotebook対象を列挙します。
    return [
        metadata_path.parent.relative_to(FRAMES_ROOT).as_posix()
        for metadata_path in sorted(FRAMES_ROOT.rglob("metadata.json"))
    ]


def notebook_name(sequence: str) -> str:
    return f"{sequence.replace('/', '_')}.ipynb"


def make_sequence_notebook(sequence: str) -> dict[str, object]:
    # 1本の動画を確認するためのNotebookテンプレートを生成します。
    # ここで作るNotebookは、代表フレーム表示・特徴点可視化・マッチング確認を行う説明用です。
    title = sequence.replace("/", " / ")
    cells = [
        markdown_cell(
            f"# {title}\n\n"
            "このノートブックは、1本の動画についてフレーム確認、歪み補正の試行、ORB特徴点検出、"
            "隣接フレームのマッチング、特徴量ファイルの確認を行うための作業場所です。"
        ),
        code_cell(
            "# このセルでは、Notebook全体で使う入力パスと対象シーケンスを定義します。\n"
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
            "# このNotebookが確認する動画シーケンスです。\n"
            f"SEQUENCE = {sequence!r}\n"
            "# 10fpsで抽出済みのフレームと、特徴量・通信量の集計結果を参照します。\n"
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
            "# 動画全体の雰囲気を見るため、先頭から末尾まで等間隔に最大6枚を選びます。\n"
            "indices = np.linspace(0, len(frame_paths) - 1, min(6, len(frame_paths)), dtype=int)\n"
            "fig, axes = plt.subplots(1, len(indices), figsize=(3.2 * len(indices), 5))\n"
            "if len(indices) == 1:\n"
            "    axes = [axes]\n"
            "for ax, index in zip(axes, indices):\n"
            "    # OpenCVはBGRで読むため、matplotlib表示用にRGBへ変換します。\n"
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
            "# feature_budgets/summary.csv から、この動画に対応する行だけを取り出します。\n"
            "budget = pd.read_csv(BUDGET_CSV)\n"
            "sequence_budget = budget[budget['sequence'] == SEQUENCE].copy()\n"
            "sequence_budget\n"
        ),
        code_cell(
            "# 教授への説明で使いやすい主要列だけを抜き出します。\n"
            "# nfeatures は特徴点数上限、good_matches は安定した対応点の目安、packet_bytes は通信量概算です。\n"
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
            "# frame_index と nfeatures を変えると、別フレーム・別特徴点数で可視化できます。\n"
            "frame_index = 0\n"
            "nfeatures = 1000\n\n"
            "# ORBは輝度変化を使うため、グレースケール画像から特徴点とdescriptorを抽出します。\n"
            "image_bgr = cv2.imread(str(frame_paths[frame_index]))\n"
            "gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)\n"
            "orb = cv2.ORB_create(nfeatures=nfeatures)\n"
            "keypoints, descriptors = orb.detectAndCompute(gray, None)\n"
            "# DRAW_RICH_KEYPOINTS で特徴点の位置・向き・スケールを可視化します。\n"
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
            "# ここでは仮の内部パラメータを使い、歪み補正の処理手順だけを確認します。\n"
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
            "# 隣接する2フレームでORB特徴量を対応付け、追跡しやすさを確認します。\n"
            "i = 0\n"
            "j = min(i + 1, len(frame_paths) - 1)\n"
            "img1_gray = cv2.imread(str(frame_paths[i]), cv2.IMREAD_GRAYSCALE)\n"
            "img2_gray = cv2.imread(str(frame_paths[j]), cv2.IMREAD_GRAYSCALE)\n\n"
            "kp1, des1 = orb.detectAndCompute(img1_gray, None)\n"
            "kp2, des2 = orb.detectAndCompute(img2_gray, None)\n"
            "# ORB descriptor はバイナリなので、Hamming距離でマッチングします。\n"
            "matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)\n"
            "matches = [] if des1 is None or des2 is None else matcher.match(des1, des2)\n"
            "matches = sorted(matches, key=lambda match: match.distance)\n"
            "# distance <= 64 を、後続の姿勢推定に使えそうな良いマッチの目安にしています。\n"
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
            "# export_orb_features.py が保存した特徴量ファイルを読み込み、中身の形を確認します。\n"
            "feature_file = FEATURES_ROOT / SEQUENCE / f'{frame_paths[frame_index].stem}.npz'\n"
            "with np.load(feature_file) as feature_data:\n"
            "    # keypoints は [x, y, size, angle, response, octave, class_id] の数値配列です。\n"
            "    saved_keypoints = feature_data['keypoints']\n"
            "    # descriptors は [特徴点数, 32] のORBバイナリ記述子です。\n"
            "    saved_descriptors = feature_data['descriptors']\n\n"
            "feature_file, saved_keypoints.shape, saved_descriptors.shape, saved_descriptors.dtype\n"
        ),
        markdown_cell(
            "## Essential Matrixの最小確認\n\n"
            "仮のカメラ内部パラメータなので、ここでの値は精度評価ではなく、処理パイプラインの確認用です。"
        ),
        code_cell(
            "# Essential Matrixは2枚の画像間の相対姿勢推定に使う行列です。\n"
            "# ここでは仮キャリブレーションなので、精度評価ではなく処理確認として見ます。\n"
            "if len(matches) >= 8:\n"
            "    # マッチから、1枚目と2枚目の対応点座標を取り出します。\n"
            "    pts1 = np.float32([kp1[match.queryIdx].pt for match in matches])\n"
            "    pts2 = np.float32([kp2[match.trainIdx].pt for match in matches])\n"
            "    # RANSACで外れ値マッチを除きながらEssential Matrixを推定します。\n"
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
    # 生成した動画別Notebookへのリンク一覧を作ります。
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
    # Jupyter NotebookはJSONファイルなので、辞書を整形して書き出します。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    sequences = iter_sequences()
    if not sequences:
        raise SystemExit(f"No metadata.json files found under {FRAMES_ROOT}")

    # index Notebookと、各動画ごとのNotebookをまとめて再生成します。
    write_notebook(NOTEBOOK_DIR / "00_video_index.ipynb", make_index_notebook(sequences))
    for sequence in sequences:
        write_notebook(NOTEBOOK_DIR / notebook_name(sequence), make_sequence_notebook(sequence))

    print(f"Wrote {len(sequences) + 1} notebooks to {NOTEBOOK_DIR}")


if __name__ == "__main__":
    main()
