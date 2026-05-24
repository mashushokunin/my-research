# Results

実験結果、評価値、出力画像、ログを保存するディレクトリです。

## Policy

- 実験ごとに日時や実験名でサブディレクトリを作ります。
- 実験条件は `configs/` 側に保存し、結果から参照できるようにします。
- 大きな画像、動画、ログ、モデルファイルはGit管理しません。

## Suggested Layout

```text
results/
└── YYYYMMDD_experiment_name/
    ├── metrics.csv
    ├── summary.md
    ├── figures/
    └── logs/
```
