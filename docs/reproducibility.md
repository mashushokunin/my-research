# Reproducibility Policy

このリポジトリでは、Mac上またはMATLAB OnlineでのMATLAB実験を再開できるように、Git管理するものと外部管理するものを分けます。既存のPython・Jetson実験も研究履歴として維持します。

## Gitで管理するもの

- 実装コード: `src/`, `experiments/`, `simulink/`
- 既存の実装資産: `scripts/`, `apps/`, `patches/`
- 実行設定: `configs/`
- 既存のJetson環境構築: `deploy/jetson/`
- 小さいモデルやキャリブレーション結果: `models/`
- 実験メタデータ: `data/metadata/`
- 小さい要約結果: `results/**/summary.csv`, `results/**/group_summary.csv`, `results/**/sequence_summary.csv`, `results/**/ate_summary.csv`
- 研究メモと再現手順: `docs/`, `README.md`
- MATLABソース、Live Script、Simulinkモデル: `*.m`, `*.mlx`, `*.slx`

## Gitで管理しないもの

- 生動画や大きな画像
- 抽出フレーム
- `.npz` などの大きな特徴量ファイル
- ORB-SLAM3やPangolinなどの外部リポジトリとビルド成果物
- 大きい学習済みモデル
- ログ、接触シート、軌跡テキストなど再生成できる結果
- MATLAB/Simulinkの自動保存、キャッシュ、生成コード

## MATLAB実験を再開する流れ

1. MATLABまたはMATLAB Onlineでリポジトリを開きます。
2. 必要なToolboxを確認します。
3. EuRoCを`data/euroc/`へ配置します。
4. `configs/matlab/`の実験条件を確認します。
5. `experiments/`の対象実験を実行し、結果を`results/`へ保存します。

## 既存のJetson実験を再開する流れ

1. Jetsonでリポジトリをcloneします。
2. `deploy/jetson/install.sh` で依存関係と外部リポジトリを準備します。
3. `configs/jetson/default.yaml` を実機のカメラ設定に合わせます。
4. `models/` にある小さいモデルやキャリブレーション結果を参照します。
5. 大きな成果物が必要な場合は `artifacts/README.md` の取得方法に従います。

## 大きな成果物を追加するとき

大きなファイルをGitに入れる前に、以下を `artifacts/README.md` に記録します。

```text
name:
path:
source:
created_from_commit:
created_by_command:
notes:
```

通常のGitで管理するか、Git LFS、DVC、Google Driveなどの外部管理にするかを、ファイルサイズと更新頻度で判断します。
