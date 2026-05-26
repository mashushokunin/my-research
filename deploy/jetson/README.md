# Jetson Deploy

Jetsonへの環境構築、デプロイ、自動起動に関するファイルを置きます。

## Candidates

- `install.sh`: Jetson上で必要な依存関係を入れるスクリプト
- `systemd/`: 起動時にアプリを自動実行するserviceファイル
- `docker/`: Dockerfileやcompose設定

本番コード本体は `apps/jetson/` に置き、ここには実行環境を整えるためのファイルを置きます。
