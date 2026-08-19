# Source Code

再利用する研究コードを置くディレクトリです。新しい研究実装はMATLABを基本とし、既存のPythonコードが追加される場合も機能領域ごとに整理します。

## Layout

```text
src/
├── communication/  # JPEG圧縮、特徴データの符号化、byte数計測
├── evaluation/     # 回転誤差、並進方向誤差、成功率、処理時間
├── features/       # ORB検出、記述子、マッチング、特徴点選択
└── slam/           # Essential Matrixと相対姿勢推定
```

`experiments/`で試した処理を再利用する場合は、このディレクトリへMATLAB関数として移します。実験ファイルには、条件設定、関数呼び出し、結果保存、可視化を中心に記述します。

## Implemented MATLAB functions

- `features/extractORB.m`: ORB特徴点の検出、強い特徴点の選択、ORB記述子の抽出
- `features/matchORB.m`: binary ORB記述子のマッチングと距離・処理時間の集計
