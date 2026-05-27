# SLAM Research Learning

このリポジトリは、Visual SLAMおよび協調型SLAMに関する研究・学習・実験を管理するためのものです。

## Research Theme

非構造環境における複数ロボット探索のための通信効率の高い協調型Visual SLAM

## Overview

本研究では、GPSが使えない災害現場や屋内、山道、洞窟のような非構造環境において、複数のロボットが協力して周囲の地図を作成するためのVisual SLAMについて学習・実験を行います。

特に、ロボット間で画像全体を共有するのではなく、特徴点や必要な情報のみを共有することで、通信量を削減しながら相対位置推定や地図作成を行うことを目指します。

## Directory Structure

```text
my-research/
├── apps/         # Jetsonなど実機上で動かすアプリケーションコード
├── configs/      # 実験パラメータやデータセット設定
├── data/         # データセット。大きなデータはGit管理しない
├── deploy/       # 実機へのデプロイ、起動設定、環境構築
├── docs/         # 研究テーマ、学習ログ、論文メモ、進捗記録
├── notebooks/    # 試行錯誤、可視化、簡易分析
├── results/      # 実験結果、評価値、出力画像、ログ
├── scripts/      # 実験実行や前処理のスクリプト
└── src/          # 再利用するPythonコード
```

## Source Layout

```text
src/
├── communication/  # ロボット間で共有する情報量の削減・符号化
├── evaluation/     # 精度、通信量、処理時間などの評価
├── features/       # 特徴点検出、記述子、マッチング
└── slam/           # Visual SLAMや協調SLAMの主要処理
```

## Application Layout

```text
apps/
└── jetson/         # Jetson上で実際に動かす本番寄りコード
    ├── camera/     # 実機カメラ入力に関する処理
    ├── runtime/    # 実行ループ、ログ、状態管理
    └── main.py     # Jetsonアプリの起動入口
```

Jetson固有の設定は `configs/jetson/` に置き、セットアップや自動起動に関するファイルは `deploy/jetson/` に置きます。

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Git Policy

- `data/raw/`, `data/interim/`, `data/processed/` はGit管理しません。
- 小さな確認用データだけ `data/sample/` に置きます。
- 実験結果は `results/` に保存しますが、大きな出力はGit管理しません。
- 実験条件は `configs/` に保存し、再現できる形で残します。
