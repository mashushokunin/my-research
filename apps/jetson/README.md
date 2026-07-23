# Jetson Application

Jetson上で実際に起動する本番寄りコードを置くディレクトリです。

## Layout

```text
apps/jetson/
├── camera/      # カメラ入力、デバイス初期化、フレーム取得
├── runtime/     # 実行ループ、ログ、状態管理
├── main.py      # 起動入口
└── requirements-jetson.txt
```

## Policy

- 研究ロジックとして再利用したい処理は `src/` に置きます。
- Jetson固有の入出力、実機制御、起動処理は `apps/jetson/` に置きます。
- Jetson用の設定ファイルは `configs/jetson/` に置きます。
- インストール、自動起動、デプロイ手順は `deploy/jetson/` に置きます。

## Run

```bash
python3 apps/jetson/main.py --config configs/jetson/default.yaml
```

設定だけ確認する場合:

```bash
python3 apps/jetson/main.py --config configs/jetson/default.yaml --dry-run
```

## Prerequisites

- Jetson上でOpenCVからカメラを開けること。
- `python3-opencv` と `pyyaml` が入っていること。
- `run_orbslam: true` にする場合は、ORB-SLAM3 と Pangolin がビルド済みであること。
- `configs/jetson/default.yaml` の `settings` は現在近似キャリブレーション値です。軌跡精度を評価する前に実測値へ置き換えてください。

Jetson上の依存関係とORB-SLAM3/Pangolinを準備する例:

```bash
bash deploy/jetson/install.sh
```

## Runtime Behavior

`apps/jetson/main.py` は `configs/jetson/default.yaml` を読み込み、以下を行います。

1. OpenCVで `camera_device` を開く。
2. `camera_width`, `camera_height`, `camera_fps` を設定する。
3. `max_frames` または `duration_sec` まで連続フレームを取得する。
4. `output_dir/sequence_name/frames/` に `frame_000000.jpg` 形式で保存する。
5. `frames.csv`, `metadata.json`, `rgb.txt` を作る。
6. `run_orbslam: true` の場合、ORB-SLAM3の `mono_tum` をそのシーケンスに対して実行する。

保存だけ行い、あとから既存スクリプトで実行する場合は、`run_orbslam: false` のままにします。Jetsonで保存したシーケンスは `rgb.txt` を含むため、`scripts/run_orbslam3_monocular.py` と同じ `mono_tum` 形式に合わせています。

保存後に既存スクリプトでORB-SLAM3を実行する例:

```bash
python3 scripts/run_orbslam3_monocular.py \
  --sequence-root results/jetson \
  --only jetson_live \
  --output-root results/jetson_orbslam3 \
  --orbslam-root ../external-repos/ORB_SLAM3 \
  --pangolin-build ../external-repos/Pangolin/build \
  --settings configs/orbslam3/iphone_vertical_1080x1920_approx.yaml
```

## Camera Notes

USBカメラの場合は通常 `camera_device: 0` と `camera_backend: auto` または `v4l2` を使います。

CSIカメラでGStreamerが必要な場合は、`camera_backend: gstreamer` と `gst_pipeline` を設定します。例:

```yaml
camera_backend: gstreamer
gst_pipeline: "nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1280, height=720, framerate=30/1 ! nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink"
```
