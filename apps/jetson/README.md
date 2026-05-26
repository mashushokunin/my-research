# Jetson Application

Jetson上で実際に起動する本番寄りコードを置くディレクトリです。

## Layout

```text
apps/jetson/
├── camera/      # カメラ入力、デバイス初期化、フレーム取得
├── runtime/     # 実行ループ、ログ、状態管理
├── main.py      # 起動入口
└── requirements-jetson.txt
```

## Policy

- 研究ロジックとして再利用したい処理は `src/` に置きます。
- Jetson固有の入出力、実機制御、起動処理は `apps/jetson/` に置きます。
- Jetson用の設定ファイルは `configs/jetson/` に置きます。
- インストール、自動起動、デプロイ手順は `deploy/jetson/` に置きます。

## Run

```bash
python apps/jetson/main.py --config configs/jetson/default.yaml
```
