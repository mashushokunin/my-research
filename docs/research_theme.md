# Research Theme

## Title

通信帯域制約下の協調Visual SLAMにおける画像・特徴点・記述子の通信量と姿勢推定性能の比較

**English:** Comparative Evaluation of Shared Visual Information for Cooperative Visual SLAM under Bandwidth Constraints

## Motivation

複数ロボットがVisual SLAMを行う場合、観測情報の共有によって自己位置推定や地図の整合性を改善できます。一方、画像全体の共有は通信量が大きく、情報を削減しすぎると視覚対応や相対姿勢推定に失敗する可能性があります。本研究では、少ない通信量で必要な推定性能を維持できる共有方法を調べます。

## Focus

- 圧縮画像、全特徴点＋記述子、選択特徴点＋記述子の公平な比較
- 応答値順と空間的に均等な特徴点選択の比較
- 実際のシリアライズ後データサイズによる通信量評価
- マッチング、相対姿勢推定、処理時間とのトレードオフ評価
- MATLABによるMac上またはMATLAB Onlineでの再現可能な実験

## Initial Research Questions

- 固定された通信量の下では、どの共有方式が最も高い相対姿勢推定性能を得られるか
- 特徴点数を減らしたとき、通信量と姿勢推定性能はどのように変化するか
- 同じ特徴点数では、応答値による選択と空間的に均等な選択のどちらが有効か
- これらの傾向は、拡張実験としてSLAM全体のATEやRPEにも現れるか
