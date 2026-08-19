# Results

実験結果、評価値、出力画像、ログを保存するディレクトリです。

## Policy

- 実験ごとに日時や実験名でサブディレクトリを作ります。
- 実験条件は `configs/` 側に保存し、結果から参照できるようにします。
- 大きな画像、動画、ログ、特徴量ファイルはGit管理しません。
- 小さい `summary.csv`, `group_summary.csv`, `sequence_summary.csv`, `ate_summary.csv` は、研究の再現性と比較のためGit管理できます。
- MATLAB実験の横断比較に使う小さいCSVは`results/csv/`へ置けます。
- MATLAB実験ごとの出力は`results/matlab/<experiment_id>/`へ置きます。
- 実験から生成した図は`results/figures/`へ置きます。
- JetsonやPC実行に必要な小さいモデル、キャリブレーション結果は `models/` に置きます。

## Suggested Layout

```text
results/
├── csv/                     # 横断比較用の小さい要約CSV
├── figures/                 # 実験から生成した図
├── matlab/                  # MATLAB実験ごとの結果
└── YYYYMMDD_experiment_name/
    ├── metrics.csv          # 大きい詳細結果はGit管理しない
    ├── summary.csv          # 小さい要約はGit管理可能
    └── logs/
```
