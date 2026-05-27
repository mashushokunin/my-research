# Scripts

実験実行、データ前処理、評価、可視化のためのスクリプトを置くディレクトリです。

Notebookで固めた処理は、再実行できるようにスクリプト化します。

## Video Preprocessing

動画一覧を作成します。

```bash
python scripts/video_inventory.py
```

確認用に低FPSでフレーム抽出します。

```bash
python scripts/extract_frames.py --fps 2
```

既存の抽出結果を作り直す場合は `--overwrite` を付けます。

```bash
python scripts/extract_frames.py --fps 2 --overwrite
```

SLAMや特徴点評価でより細かく見る場合は、`--fps 10` などに上げます。出力先は `data/interim/frames/` で、Git管理しません。

抽出したフレームから ORB 特徴点数と隣接フレーム間マッチ数を集計します。

```bash
python scripts/analyze_orb_features.py
```

出力先は `results/orb_baseline/` です。

複数の特徴点数上限で、特徴点・記述子の通信量と隣接フレームマッチ数を比較します。

```bash
python scripts/evaluate_feature_budgets.py
```

出力先は `results/feature_budgets/summary.csv` です。`compact_packet_bytes` は、各特徴点につき `x, y, angle, octave, response` を量子化して送り、ORB descriptor 32 bytes を添える想定の概算です。

各フレームの ORB keypoint と descriptor を `.npz` として保存します。

```bash
python scripts/export_orb_features.py --nfeatures 1000
```

出力先は `results/orb_features_n1000/` です。各 `.npz` には `keypoints` と `descriptors` が入ります。

代表フレームを並べた目視確認用のコンタクトシートを作成します。

```bash
python scripts/make_contact_sheets.py
```

出力先は `results/contact_sheets/` です。プライバシー確認、ブレ、暗さ、撮影経路の確認に使います。

## ORB-SLAM3 Preparation

ORB-SLAM3 の `mono_tum` で読み込める `rgb.txt` を作成します。SLAM 用には確認用の `2 fps` より `10 fps` 以上を使います。

```bash
python scripts/extract_frames.py --fps 10 --output-root data/interim/frames_10fps --overwrite
python scripts/prepare_orbslam_tum.py
```

設定ファイルのたたき台は `configs/orbslam3/iphone_vertical_1080x1920_approx.yaml` です。これは仮の内部パラメータなので、軌跡精度を評価する前にカメラキャリブレーション値へ置き換えます。

ORB-SLAM3 の `mono_tum` を全シーケンスに実行します。

```bash
python scripts/run_orbslam3_monocular.py
```

出力先は `results/orbslam3_monocular/` です。各シーケンスの `run.log` と `KeyFrameTrajectory.txt` を確認します。

実行結果を一覧化します。

```bash
python scripts/summarize_orbslam3_runs.py
```

出力は `results/orbslam3_monocular/summary.csv` です。
