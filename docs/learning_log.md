# Learning Log

Visual SLAM、協調SLAM、特徴点マッチング、評価方法に関する学習記録を残します。

## Template

```text
## YYYY-MM-DD

### Topic

### What I learned

### Questions

### Next actions
```

## Entries

## 2026-05-27

### Topic

撮影済み動画の前処理準備

### What I learned

- `structured` に5本、`unstructured_like` に3本の動画がある。
- 8本すべて OpenCV で読み込み可能。
- 解像度は `1080x1920`、FPS は約30。
- 確認用として `2 fps` で合計197枚のフレームを抽出した。
- ORB特徴点は `nfeatures=1000` では全フレームで上限に達した。今回の動画は特徴点が十分多い。
- ORB descriptor だけを共有する場合、`nfeatures=1000` では1フレームあたり約32,000 bytes、`nfeatures=2000` では最大約64,000 bytes が目安になる。

### Questions

- 各動画に個人情報、顔、掲示物などが写っていないか、コンタクトシートで目視確認する。
- `structured` と `unstructured_like` の差を見るには、特徴点数だけでなく、マッチ数、追跡ロスト、SLAM軌跡の安定性を見る必要がある。

### Next actions

- `results/contact_sheets/` を見て、プライバシーと画質を確認する。
- 問題がない動画を使って、ORB-SLAM3 の単眼ベースラインを実行する。
- 通信量評価では、特徴点数を `500`, `1000`, `2000` などに変えて精度と通信量の関係を見る。

## 2026-05-27

### Topic

ORB-SLAM3 単眼ベースライン

### What I learned

- macOS で ORB-SLAM3 をビルドするために、CMake 4、Eigen 5、AppleClang 向けの互換パッチが必要だった。
- Homebrew の `pangolin` は ORB-SLAM3 用ライブラリではなくVPNアプリだったため、`external-repos/Pangolin` に C++ ライブラリ版を clone してビルドした。
- SLAM用に `10 fps` で合計968枚のフレームを抽出し、ORB-SLAM3 `mono_tum` 用の `rgb.txt` を8本分作成した。
- 8本すべて ORB-SLAM3 の実行自体は完了した。
- `structured_IMG_5983` は初期化後に local map tracking 失敗が多く、`KeyFrameTrajectory.txt` が空だった。
- その他7本はキーフレーム軌跡が保存された。

### Questions

- 現在のカメラ内部パラメータは仮値なので、軌跡の形や絶対精度はまだ評価対象にしない。
- `structured_IMG_5983` の失敗要因は、撮影動作、ブレ、視差不足、仮キャリブレーションの影響を切り分ける必要がある。

### Next actions

- `results/orbslam3_monocular/summary.csv` をもとに成功・失敗ケースを整理する。
- カメラキャリブレーションを行い、`configs/orbslam3/iphone_vertical_1080x1920_approx.yaml` を実測値に置き換える。
- 特徴点数、descriptor量、SLAM成功率を並べて通信量削減の基礎評価表を作る。

## 2026-05-27

### Topic

特徴点・記述子の通信量評価

### What I learned

- `10 fps` 抽出フレーム968枚に対して、ORB特徴点上限 `250`, `500`, `1000`, `2000` の比較表を作成した。
- `nfeatures=1000` の ORB keypoint と descriptor を全フレーム分 `.npz` に保存した。
- `nfeatures=250` でも structured では平均約168 matches、unstructured_like では平均約142 matches が得られた。
- compact packet 想定では、`nfeatures=250` は約10KB/frame、`nfeatures=1000` は約40KB/frame。
- JPEGフレーム送信と比べると、compact packet は `nfeatures=250` で約1%から2%、`nfeatures=1000` で約4%から7%程度だった。

### Questions

- SLAMや相対位置推定に必要な最低マッチ数をどこに置くか決める必要がある。
- 非構造環境もどきでは structured より平均マッチ数が少なく、match distance も大きい傾向があるため、単純な特徴点数削減だけでは失敗ケースが増える可能性がある。

### Next actions

- `results/feature_budgets/group_summary.csv` を使って、特徴点数と通信量のトレードオフ表を作る。
- `results/orb_features_n1000/` の `.npz` を使って、フレーム間または動画間の特徴点マッチング実験に進む。
- 次の候補として、`nfeatures=250/500/1000` の特徴点で相対姿勢推定が成立するかを RANSAC essential matrix で評価する。
