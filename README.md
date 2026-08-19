# Cooperative Visual SLAM Research

このリポジトリは、通信帯域制約下の協調Visual SLAMに関する研究、実験、評価結果を管理するためのものです。現在はMacからMATLABまたはMATLAB Onlineを使用して研究を進めます。

## Research Theme

**通信帯域制約下の協調Visual SLAMにおける画像・特徴点・記述子の通信量と姿勢推定性能の比較**

英語案: **Comparative Evaluation of Shared Visual Information for Cooperative Visual SLAM under Bandwidth Constraints**

## Overview

複数ロボット間で共有する視覚情報を、圧縮画像、全特徴点＋記述子、選択特徴点＋記述子に分け、同一条件で通信量と推定性能を比較します。固定された通信量の中で、どの共有方式が相対姿勢推定に最も有効かを明らかにすることが目標です。

最初の必須範囲は、公開データセットを用いた2視点の特徴点マッチングと相対姿勢推定です。ORB-SLAM3によるATEやRPEなどの軌跡評価は拡張範囲として扱います。

## Research Environment

- macOS
- [MATLAB Online](https://matlab.mathworks.com/) またはMac版MATLAB
- Computer Vision Toolbox
- Simulink（通信帯域、遅延、送信周期などを模擬する場合）
- EuRoC MAV Dataset（第一候補）

## Directory Structure

```text
my-research/
├── apps/         # 既存のJetson向けアプリケーション資産
├── artifacts/    # Git管理しない大きな成果物の取得方法
├── configs/      # 実験パラメータやデータセット設定
│   ├── matlab/   # MATLAB実験設定
│   ├── jetson/   # 既存のJetson設定
│   └── orbslam3/ # 既存のORB-SLAM3設定
├── data/         # データセット。大きなデータはGit管理しない
├── deploy/       # 既存の実機デプロイ・環境構築資産
├── docs/         # 研究テーマ、学習ログ、論文メモ、進捗記録
├── experiments/  # MATLABの再現可能な実験エントリーポイント
├── models/       # 小さいモデル・キャリブレーション
├── notebooks/    # 既存のJupyter Notebook資産
├── patches/      # 外部SLAM実装向けの既存パッチ
├── results/      # 実験結果、評価値、出力画像、ログ
├── scripts/      # 既存のPython実験・前処理スクリプト
├── simulink/     # 通信条件を模擬するSimulinkモデル
└── src/          # 再利用する研究コード。新規実装はMATLABを基本とする
```

## Source Layout

```text
src/
├── communication/  # JPEG圧縮、特徴データの符号化、byte数計測
├── evaluation/     # 回転誤差、並進方向誤差、成功率、処理時間
├── features/       # ORB検出、記述子、マッチング、特徴点選択
└── slam/           # Essential Matrixと相対姿勢推定
```

## MATLAB Experiment Flow

```text
EuRoC画像ペアの読み込み
        ↓
ORB特徴点・記述子の抽出
        ↓
共有方式ごとの送信データ作成とbyte数計測
        ↓
特徴点マッチングとRANSAC
        ↓
Essential Matrixから相対姿勢を推定
        ↓
正解姿勢との比較
        ↓
通信量と推定性能をCSV・グラフで評価
```

最初の実験計画は[experiments/README.md](experiments/README.md)を参照してください。

## Setup

1. MATLABまたはMATLAB Onlineでこのリポジトリを開きます。
2. Command Windowで`setup_matlab_project`を実行し、MATLAB Projectを生成します。
3. Computer Vision Toolboxが利用できることを確認します。
4. EuRoCを`data/euroc/`へ配置します。このディレクトリはGit管理しません。

詳しいProject初期化手順は[docs/matlab_project_setup.md](docs/matlab_project_setup.md)を参照してください。

最初のORBベースラインを実行するには、Command Windowで次を実行します。

```matlab
summary = exp01_orb_baseline
```

既存のPython環境を再現する必要がある場合のみ、`requirements.txt`と`scripts/README.md`を参照してください。

## Legacy Assets

`apps/jetson/`、`deploy/jetson/`、`notebooks/`、`scripts/`、`patches/orbslam3/`は、Jetson＋Python＋ORB-SLAM3を中心に進めていた時期の研究資産です。MATLAB移行後も研究履歴と比較用実装として残し、明示的な整理方針が決まるまでは削除しません。

## Git Policy

- `data/raw/`, `data/interim/`, `data/processed/` はGit管理しません。
- EuRoCは`data/euroc/`に置き、Git管理しません。
- 小さな確認用データだけ `data/sample/` に置きます。
- MATLABの`.m`、Live Scriptの`.mlx`、Simulinkモデルの`.slx`はGit管理します。
- MATLAB/Simulinkの自動保存ファイル、キャッシュ、生成コードはGit管理しません。
- 大きなモデル、動画、抽出フレーム、ビルド成果物は `artifacts/` や外部ストレージで管理し、取得方法だけを残します。
- 実験結果は`results/`に保存しますが、大きな出力はGit管理しません。小さい要約CSVは再現性のため管理できます。
- 実験条件は `configs/` に保存し、再現できる形で残します。

詳しい運用ルールは `docs/reproducibility.md` にまとめています。
