# PC Experiment Plan

Jetsonが使えない間は、既存動画と抽出済みフレームで「SLAM前に分かること」を固めます。

## 目的

SLAMの最終成否だけを見る前に、通信量を抑えた特徴点共有がどの程度使えそうかを評価します。

## 今すぐできる実験

1. 特徴点数と通信量の比較
   - `scripts/evaluate_feature_budgets.py`
   - `nfeatures = 250, 500, 1000, 2000` で、特徴点数、良いマッチ数、JPEG比の通信量を比較します。

2. SLAM前の幾何評価
   - `scripts/evaluate_preslam_geometry.py`
   - フレーム間マッチ、RANSAC inlier、特徴点の空間分布、明るさ、ブレ指標を比較します。

3. 特徴点選択方法の比較
   - `scripts/evaluate_feature_selection.py`
   - `top_response`, `grid`, `random` を同じ送信特徴点数で比較します。

4. 図表作成
   - `scripts/plot_preslam_results.py`
   - 研究説明に使う図を `results/figures/` に出力します。

## 実行例

```bash
python scripts/evaluate_feature_budgets.py
python scripts/evaluate_preslam_geometry.py --max-pairs-per-sequence 80
python scripts/evaluate_feature_selection.py --max-pairs-per-sequence 80
python scripts/plot_preslam_results.py
```

全フレームで評価する場合は `--max-pairs-per-sequence 0` を使います。

## 見るべき指標

- `avg_good_matches_to_previous`
- `avg_fundamental_inliers`
- `avg_fundamental_inlier_ratio`
- `avg_occupied_grid_ratio`
- `avg_grid_entropy`
- `avg_compact_packet_vs_jpeg_ratio`

特に `fundamental_inliers` は、単なる見た目のマッチ数ではなく、幾何的に相対姿勢推定へ使えそうな対応点数の目安です。

## 次に撮影したいデータ

- Jetson実機のUSBカメラ映像
- 同じ経路を明るい条件と暗い条件で撮った映像
- ゆっくり移動と速く移動の比較映像
- 特徴点が少ない壁・床が多い映像
- 物が多く散らかった非構造環境に近い映像

これらがあると、通信量削減だけでなく「どの環境で破綻しやすいか」まで説明できます。
