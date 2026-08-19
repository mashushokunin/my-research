# ORB-SLAM3 EuRoC Experiment

公開データセットで単体SLAMを安定して動かすための最小実験基盤です。

## 目的

Jetson実機や複数ロボット実験に進む前に、同じ入力と同じ設定でORB-SLAM3を再実行できる状態を作ります。

確認する条件:

- ORB-SLAM3が最後まで停止せずに動く
- `KeyFrameTrajectory.txt` を保存できる
- `run.log` を保存できる
- ATE RMSEを計算できる
- 実行時間を保存できる
- 同じ条件で再実行したとき、おおむね同じ結果になる

## データ配置

EuRoCは大きいためGit管理しません。以下のどちらかの名前で配置します。

```text
data/euroc/
└── MH_01_easy/
    └── mav0/
        ├── cam0/
        │   ├── data.csv
        │   └── data/
        └── state_groundtruth_estimate0/
            └── data.csv
```

ORB-SLAM3の公式サンプルに合わせた短い名前でも動きます。

```text
data/euroc/
└── MH01/
    └── mav0/
```

最初は `MH_01_easy` または `V1_01_easy` の1シーケンスで十分です。

## ORB-SLAM3実行

```bash
python scripts/run_orbslam3_euroc.py \
  --dataset-root data/euroc \
  --sequence MH_01_easy \
  --output-root results/orbslam3_euroc \
  --overwrite
```

デフォルトでは以下を使います。

- ORB-SLAM3 root: `../external-repos/ORB_SLAM3`
- binary: `../external-repos/ORB_SLAM3/Examples/Monocular/mono_euroc`
- settings: `../external-repos/ORB_SLAM3/Examples/Monocular/EuRoC.yaml`
- timestamps: `../external-repos/ORB_SLAM3/Examples/Monocular/EuRoC_TimeStamps/MH01.txt`

出力:

```text
results/orbslam3_euroc/MH_01_easy/
├── run.log
├── run_summary.json
├── KeyFrameTrajectory.txt
└── CameraTrajectory.txt
```

全体要約:

```text
results/orbslam3_euroc/summary.csv
```

## ATE RMSE計算

```bash
python scripts/evaluate_trajectory_ate.py \
  --trajectory results/orbslam3_euroc/MH_01_easy/KeyFrameTrajectory.txt \
  --groundtruth data/euroc/MH_01_easy/mav0/state_groundtruth_estimate0/data.csv \
  --output-dir results/orbslam3_euroc/MH_01_easy/ate \
  --sequence MH_01_easy
```

単眼SLAMはスケールが不定になりやすいため、Sim(3)で位置軌跡を揃えてATEを計算します。

出力:

```text
results/orbslam3_euroc/MH_01_easy/ate/
├── ate_summary.csv
├── ate_associations.csv
├── sim3_rotation.txt
├── sim3_translation.txt
└── trajectory_xy.png
```

## キーフレーム単位の通信量見積もり

まずはORB-SLAM3の `KeyFrameTrajectory.txt` に出たキーフレーム時刻を使い、対応するEuRoC画像からORB特徴点を再抽出して、1キーフレームあたりの通信量を見積もります。

```bash
python scripts/estimate_keyframe_payload.py \
  --trajectory results/orbslam3_euroc/MH_01_easy/KeyFrameTrajectory.txt \
  --sequence-dir data/euroc/MH_01_easy \
  --settings ../external-repos/ORB_SLAM3/Examples/Monocular/EuRoC.yaml \
  --output-dir results/orbslam3_euroc/MH_01_easy/payload
```

出力:

```text
results/orbslam3_euroc/MH_01_easy/payload/
├── keyframe_payload.csv
└── summary.csv
```

記録するもの:

- 画像サイズ
- 画像ファイルサイズ
- 特徴点数
- descriptor行数・列数
- descriptor全体のバイト数
- 姿勢情報のバイト数
- 画像送信に対する特徴量送信の比率

このスクリプトは「ORB-SLAM3内部から直接取り出した値」ではなく、キーフレーム時刻に対応する画像から同じORB設定で再抽出した見積もりです。内部値を厳密に見る場合は、ORB-SLAM3本体にCSV出力を追加します。

## ORB-SLAM3内部値を直接CSVに出す

このリポジトリには、ORB-SLAM3側へ追加するための参考パッチを置いています。

```text
patches/orbslam3/save_keyframe_payload_csv.patch
```

適用する場合:

```bash
cd ../external-repos/ORB_SLAM3
git apply ../../my-research/patches/orbslam3/save_keyframe_payload_csv.patch
cmake --build build -j4
```

このパッチは `System::SaveKeyFramePayloadCSV()` を追加し、`mono_euroc` の終了時に以下を保存します。

```text
keyframe_payload_dataset-MH01_mono.csv
```

保存する主な列:

```text
keyframe_id
frame_id
timestamp
image_width
image_height
keypoints
descriptor_rows
descriptor_cols
descriptor_bytes
pose_float32_bytes
pose_float64_bytes
bow_words
bow_bytes_estimate
valid_mappoints
tracked_mappoints_min2
```

外部リポジトリに直接変更を入れるので、適用前に `git status` を確認してください。

## ORB-SLAM3内部で直接確認したい対象

最終的にORB-SLAM3本体側で確認したい対象:

- `Frame`
- `KeyFrame`
- `KeyPoint`
- `Descriptor`
- `MapPoint`
- `Camera Pose`
- `BoW vector`

特に1キーフレームあたり:

- `KeyFrame::N`
- `KeyFrame::mDescriptors.rows`
- `KeyFrame::mDescriptors.cols`
- `KeyFrame::mDescriptors.total() * elemSize()`
- `KeyFrame::GetPose()`
- `KeyFrame::mBowVec.size()`
- `KeyFrame::GetMapPointMatches()` の有効MapPoint数

これをCSVで出せるようになれば、「画像を送る場合」と「特徴点・記述子・姿勢・BoWを送る場合」の比較がより正確になります。
