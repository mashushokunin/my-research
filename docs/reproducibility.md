# Reproducibility Policy

このリポジトリでは、PC側の実験とJetson上の実行をできるだけ同じ状態で再開できるように、Git管理するものと外部管理するものを分けます。

## Gitで管理するもの

- 実装コード: `src/`, `scripts/`, `apps/`
- 実行設定: `configs/`
- Jetson環境構築: `deploy/jetson/`
- 小さいモデルやキャリブレーション結果: `models/`
- 実験メタデータ: `data/metadata/`
- 小さい要約結果: `results/**/summary.csv`, `results/**/group_summary.csv`, `results/**/sequence_summary.csv`
- 研究メモと再現手順: `docs/`, `README.md`

## Gitで管理しないもの

- 生動画や大きな画像
- 抽出フレーム
- `.npz` などの大きな特徴量ファイル
- ORB-SLAM3やPangolinなどの外部リポジトリとビルド成果物
- 大きい学習済みモデル
- ログ、接触シート、軌跡テキストなど再生成できる結果

## Jetsonへ持っていく流れ

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
