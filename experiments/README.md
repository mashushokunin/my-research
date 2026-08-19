# MATLAB Experiments

再現可能なMATLAB実験のエントリーポイントを置くディレクトリです。

## Planned experiments

| ID | ファイル | 目的 |
| --- | --- | --- |
| 01 | `exp01_orb_baseline.m` | 画像2枚からORB抽出・記述子生成・マッチングまでを確認する（実装済み） |
| 02 | `exp02_relative_pose.m` | Essential Matrixによる相対姿勢推定と正解姿勢との比較を行う |
| 03 | `exp03_feature_count.m` | 送信特徴点数と通信量・推定性能の関係を評価する |
| 04 | `exp04_selection_method.m` | 応答値順と空間的に均等な特徴点選択を比較する |
| 05 | `exp05_jpeg_quality.m` | JPEG品質と通信量・推定性能の関係を評価する |
| 06 | `exp06_fixed_budget.m` | 固定byte予算で共有方式を比較する |

共通処理は実験ファイルへ重複して書かず、`src/`のMATLAB関数として実装します。実験条件は`configs/matlab/`、出力は`results/`へ保存します。

## Experiment 01の実行

MATLAB Projectを開き、Command Windowで次を実行します。

```matlab
summary = exp01_orb_baseline
```

設定されたローカル画像が存在する場合は、その画像ペアを使用します。MATLAB Onlineに画像がない場合はComputer Vision Toolbox付属画像でスモークテストを行います。

出力先は`results/matlab/exp01_orb_baseline/`です。`summary.csv`の`research_input`が`true`の実行だけを研究データとして扱います。
