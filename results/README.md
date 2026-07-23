# Results

実験結果、評価値、出力画像、ログを保存するディレクトリです。

## Policy

- 実験ごとに日時や実験名でサブディレクトリを作ります。
- 実験条件は `configs/` 側に保存し、結果から参照できるようにします。
- 大きな画像、動画、ログ、特徴量ファイルはGit管理しません。
- 小さい `summary.csv`, `group_summary.csv`, `sequence_summary.csv` は、研究の再現性と比較のためGit管理できます。
- JetsonやPC実行に必要な小さいモデル、キャリブレーション結果は `models/` に置きます。

## Suggested Layout

```text
results/
└── YYYYMMDD_experiment_name/
    ├── metrics.csv
    ├── summary.md
    ├── figures/
    └── logs/
```
