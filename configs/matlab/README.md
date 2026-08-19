# MATLAB Configurations

MATLABで実行する実験の条件とデータセット設定を管理します。

## Files

- `experiment_config.m`: 入力画像、ORB、マッチング、出力先などの共通条件
- `euroc_camera.m`: EuRoCのカメラ内部パラメータとデータセット設定

設定値は実験コードへ直接埋め込まず、可能な限りこのディレクトリから読み込みます。データセットの絶対パスなど、環境ごとに異なる値や秘密情報はGit管理しません。

現在の`experiment_config.m`は、ローカルの`IMG_5978`フレームを優先します。画像が存在しないMATLAB Online環境では、Computer Vision Toolbox付属画像をExperiment 01のスモークテストに使用します。
