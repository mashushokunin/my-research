# Models

JetsonやPC側の実行に必要な、小さいモデルやキャリブレーション済みファイルを置きます。

## Policy

- `git clone` 後にすぐ使いたい小さいファイルは、このディレクトリでGit管理します。
- 目安として、数MBから数十MB程度までのファイルを対象にします。
- 大きい学習済みモデル、頻繁に更新される重み、再生成できる成果物は `artifacts/` 側で外部管理します。
- モデルを追加したら、作成条件、入力サイズ、依存する設定ファイルをこのREADMEか `configs/` に残します。

## Suggested Layout

```text
models/
├── README.md
├── calibration/      # カメラキャリブレーション結果など
└── jetson/           # Jetson実行に必要な小さいモデル
```
