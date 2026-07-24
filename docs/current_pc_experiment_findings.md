# Current PC Experiment Findings

既存の `data/interim/frames_10fps` にある8本の動画で、SLAM前評価を実行した時点のメモです。

## 実行した評価

```bash
python scripts/evaluate_preslam_geometry.py
python scripts/evaluate_feature_selection.py
MPLCONFIGDIR=/private/tmp/matplotlib-cache XDG_CACHE_HOME=/private/tmp/xdg-cache python3 scripts/plot_preslam_results.py
```

## 生成物

- `results/preslam_geometry/summary.csv`
- `results/preslam_geometry/group_summary.csv`
- `results/feature_selection/summary.csv`
- `results/feature_selection/group_summary.csv`
- `results/figures/`

`pair_metrics.csv` と図は詳細確認用で、Git管理しない想定です。

## SLAM前幾何評価の傾向

フル解像度、ORB `nfeatures=1000`、隣接フレームで比較した場合:

| group | avg good matches | avg fundamental inliers | feature/JPEG ratio |
| --- | ---: | ---: | ---: |
| structured | 652.270 | 472.144 | 0.078 |
| unstructured_like | 551.435 | 395.670 | 0.040 |

フレーム間隔を10に広げると、RANSAC inlier は大きく下がりました。

| group | frame step | avg fundamental inliers |
| --- | ---: | ---: |
| structured | 1 | 472.144 |
| structured | 10 | 182.361 |
| unstructured_like | 1 | 395.670 |
| unstructured_like | 10 | 97.138 |

この結果から、単純な特徴点マッチ数だけでなく、フレーム間隔が広がったときの幾何的inlier数が重要な指標になりそうです。

## 特徴点選択の傾向

同じ送信特徴点数で `top_response`, `grid`, `random` を比較しました。

100特徴点だけ送る場合:

| group | strategy | avg fundamental inliers | feature/JPEG ratio |
| --- | --- | ---: | ---: |
| structured | top_response | 52.810 | 0.008 |
| structured | grid | 43.668 | 0.008 |
| structured | random | 11.086 | 0.008 |
| unstructured_like | top_response | 43.213 | 0.004 |
| unstructured_like | grid | 35.568 | 0.004 |
| unstructured_like | random | 9.051 | 0.004 |

500特徴点だけ送る場合:

| group | strategy | avg fundamental inliers | feature/JPEG ratio |
| --- | --- | ---: | ---: |
| structured | top_response | 252.230 | 0.039 |
| structured | grid | 224.255 | 0.039 |
| structured | random | 101.048 | 0.039 |
| unstructured_like | top_response | 216.424 | 0.020 |
| unstructured_like | grid | 187.141 | 0.020 |
| unstructured_like | random | 75.239 | 0.020 |

現時点では、`top_response` が最も強く、`grid` はそれに近く、`random` は大きく劣ります。研究としては、次に `top_response` と `grid` を組み合わせた選択方法を試す価値があります。

## 次の実験候補

- `top_response` と `grid` を組み合わせたハイブリッド選択
- 低照度、速い移動、特徴点が少ない壁・床での撮影
- Jetsonカメラ映像に同じスクリプトを適用
- RANSAC inlier数を使った「SLAMが成功しそうか」の事前指標化
