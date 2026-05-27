# Data

研究・実験で使用する撮影データを置くディレクトリです。

## Directory Layout

```text
data/
├── structured/          # 構造環境の撮影データ
└── unstructured_like/   # 非構造環境もどきの撮影データ
```

## Notes

- `structured/` には、机、棚、廊下など形状や配置が比較的整理された環境の画像を置きます。
- `unstructured_like/` には、物が散らばっている場所や、構造が複雑に見える環境の画像を置きます。
- 大きな画像や動画をGit管理しない場合は、保存先と対応関係をこのREADMEまたは別のメモに残します。

## Current Workflow

1. `scripts/video_inventory.py` で動画一覧と基本メタデータを `data/metadata/video_inventory.csv` に保存します。
2. `data/metadata/video_inventory.csv` の `privacy_checked` と `quality_note` を確認し、個人情報や撮影品質の問題を記録します。
3. `scripts/extract_frames.py` で動画からフレームを抽出します。抽出結果は Git 管理しない `data/interim/frames/` に保存します。
4. 抽出フレームを使って、特徴点数、フレーム間マッチ数、通信量、SLAM の成否を比較します。
