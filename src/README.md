# Source Code

再利用するPythonコードを置くディレクトリです。

## Layout

```text
src/
├── communication/  # 共有情報の削減、圧縮、送受信の抽象化
├── evaluation/     # 精度、通信量、処理時間などの評価
├── features/       # 特徴点検出、記述子、マッチング
└── slam/           # Visual SLAMや協調SLAMの主要処理
```

Notebookで試した処理を再利用する場合は、このディレクトリに移してから `scripts/` から呼び出します。
