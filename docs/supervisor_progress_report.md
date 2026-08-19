# 研究進捗説明レポート

## 1. 研究テーマ

本研究のテーマは「非構造環境における複数ロボット探索のための通信効率の高い協調型Visual SLAM」です。

GPSが使えない屋内、災害現場、山道、洞窟のような環境では、単一ロボットだけで広範囲を探索することが難しい場合があります。複数ロボットがVisual SLAMを用いて協調すれば、探索範囲の拡大や地図作成の効率化が期待できます。一方で、ロボット間通信には帯域制約があり、画像全体や大きな地図情報をそのまま共有すると通信量が大きくなります。

そこで本研究では、画像全体を送るのではなく、Frame、KeyFrame、KeyPoint、Descriptor、MapPoint、Camera Pose、BoW vectorなど、SLAM内部で実際に使われる情報のうち、どの情報を共有すれば通信量を抑えながら自己位置推定や地図統合に有効かを調べます。

## 2. 現時点で説明できる結論

まだJetson実機を用いた本番実験には入れていませんが、研究の前段階として重要な実装と評価は進められています。

現時点で説明できることは次のとおりです。

- 研究ディレクトリを、PC実験、Jetson実行、データ、結果、設定、ドキュメントに分けて整理した。
- Jetsonで撮影、保存、ORB-SLAM3実行へつなげるための実行コードを用意した。
- PC上の撮影動画から、ORB特徴量、特徴点マッチ、RANSACによる幾何的inlier数、通信量概算を評価できるようにした。
- 特徴点数や特徴点選択方法を変えたとき、通信量と幾何的対応点数がどう変化するかを比較した。
- ORB-SLAM3を公開データセットEuRoCで実行し、ログ、軌跡、ATE RMSE、実行時間、キーフレーム単位の通信量を保存するための実験基盤を追加した。

したがって、Jetsonが一時的に使えない場合でも、公開データセットを用いて、通信帯域制約下の協調Visual SLAMの基礎実験は進められます。特に、画像、キーフレーム、特徴点、記述子、姿勢情報の共有方式による通信量と自己位置推定精度の違いは、PC上で再現可能です。

ただし、Jetson実機は不要になったわけではありません。Jetsonでは、実時間処理、カメラキャリブレーション、CPU/GPU負荷、発熱、消費電力、実際の通信遅延、照明変化や手ブレなどを確認する必要があります。PCと公開データセットで基礎評価を固め、Jetsonでは実機制約を検証する、という切り分けが妥当です。

## 3. これまでに実装した内容

### 3.1 リポジトリ整理と再現性の方針

研究を再開しやすくするため、ディレクトリ構成を整理しました。

- `apps/jetson/`: Jetson上で動かす実行コード
- `configs/`: 実験設定、ORB-SLAM3設定、Jetson設定
- `data/`: データセット、動画メタデータ
- `docs/`: 研究テーマ、再現性、実験計画、進捗メモ
- `scripts/`: 解析、前処理、評価、ORB-SLAM3実行スクリプト
- `results/`: 小さい要約結果、図、ログ
- `patches/`: 外部リポジトリへ適用する参考パッチ

実装で意識した点は、再現性を保つことです。生動画やEuRoCのような大きなデータはGitに入れず、コード、設定、小さい要約CSV、手順書をGitで管理します。これにより、PCでもJetsonでも同じコマンドで再実行しやすくなります。

### 3.2 Jetson用実行基盤

Jetson用には、`apps/jetson/main.py` と `configs/jetson/default.yaml` を中心に、カメラ入力、フレーム保存、メタデータ保存、ORB-SLAM3実行へつなげる構成を用意しました。

この実装では、Jetson上で取得した画像列をあとからORB-SLAM3に渡せるように、`frames/`、`frames.csv`、`metadata.json`、`rgb.txt` を保存する方針にしています。`rgb.txt` を作ることで、ORB-SLAM3のTUM形式入力に合わせやすくなります。

現時点では、Jetson実機で十分な実験はできていません。しかし、Jetsonが再び使えるようになったときに、撮影、保存、PC側評価、ORB-SLAM3実行までつながる入口は準備済みです。

### 3.3 PC上でのSLAM前評価

Jetsonが使えない間にも研究を止めないため、PC上の動画を使って、SLAMの前に分かる指標を評価しました。

対象データは、構造的な環境を撮った動画5本と、非構造環境に近い動画3本です。動画はおおむね1080 x 1920、30fps、9秒から16秒程度です。

実装した評価は次のとおりです。

- `scripts/evaluate_feature_budgets.py`: ORB特徴点数を250、500、1000、2000に変えたときの通信量とマッチ数を比較
- `scripts/evaluate_preslam_geometry.py`: 隣接フレーム間の特徴点マッチ、Fundamental matrixのRANSAC inlier、Homography inlier、特徴点分布、画像品質を比較
- `scripts/evaluate_feature_selection.py`: 同じ送信特徴点数で、`top_response`、`grid`、`random` の選択方法を比較
- `scripts/plot_preslam_results.py`: 結果説明用の図を生成

SLAMは最終的には地図と軌跡の精度で評価しますが、その前段階として、特徴点対応が幾何的にどれだけ使えるかを見ることが重要です。そのため、単なるマッチ数だけでなく、Fundamental matrixをRANSACで推定したときのinlier数を評価指標にしました。

### 3.4 ORB-SLAM3実行基盤

既存動画に対してORB-SLAM3 monocularを動かし、`KeyFrameTrajectory.txt` と `run.log` を保存する実験を行いました。地上真値がないためATEは計算できませんが、ORB-SLAM3がどの動画で初期化し、どの程度キーフレームを作るかを確認する段階まで進んでいます。

さらに、公開データセットEuRoCを使った最小実験基盤を追加しました。

- `scripts/run_orbslam3_euroc.py`: EuRoCの1シーケンスをORB-SLAM3で実行し、ログ、軌跡、実行時間を保存
- `scripts/evaluate_trajectory_ate.py`: EuRoCのground truthとORB-SLAM3軌跡からATE RMSEを計算
- `scripts/estimate_keyframe_payload.py`: キーフレーム時刻に対応する画像からORB特徴量を再抽出し、通信量を見積もる
- `patches/orbslam3/save_keyframe_payload_csv.patch`: ORB-SLAM3内部のKeyFrame情報を直接CSV保存するための参考パッチ

EuRoCデータセットを配置すれば、`MH_01_easy` または `V1_01_easy` の1シーケンスから、単体SLAMの安定実行、軌跡保存、ATE計算、通信量見積もりまで確認できます。

## 4. 現在得られている結果

### 4.1 特徴量送信は画像送信より大幅に小さい

ORB descriptorは1特徴点あたり32 bytesです。現在の概算では、descriptorに加えて量子化したkeypoint情報を送るcompact packetを、1特徴点あたり41 bytesとして評価しています。

PC動画での特徴点数別の平均通信量は次の傾向でした。

| group | nfeatures | compact packet | JPEG画像 | compact/JPEG |
| --- | ---: | ---: | ---: | ---: |
| structured | 500 | 20.02 KB/frame | 595.95 KB/frame | 3.68% |
| unstructured_like | 500 | 20.02 KB/frame | 1065.62 KB/frame | 1.92% |
| structured | 1000 | 40.00 KB/frame | 595.95 KB/frame | 7.34% |
| unstructured_like | 1000 | 40.04 KB/frame | 1065.62 KB/frame | 3.85% |
| structured | 2000 | 79.57 KB/frame | 595.95 KB/frame | 14.60% |
| unstructured_like | 2000 | 80.08 KB/frame | 1065.62 KB/frame | 7.70% |

この結果から、画像全体を送る場合に比べ、特徴点と記述子だけを送る方式は通信量を大幅に削減できる見込みがあります。

### 4.2 フレーム間隔が広がると幾何的inlierが減る

フル解像度、ORB `nfeatures=1000`、隣接フレームで比較した場合、構造的環境では平均good matchesが約652、Fundamental matrixの平均inlierが約472でした。非構造環境に近い動画では、平均good matchesが約551、平均inlierが約396でした。

一方で、フレーム間隔を10に広げると、平均inlierは大きく下がりました。

| group | frame step | avg fundamental inliers |
| --- | ---: | ---: |
| structured | 1 | 472.144 |
| structured | 10 | 182.361 |
| unstructured_like | 1 | 395.670 |
| unstructured_like | 10 | 97.138 |

これは、通信量を減らすために送信頻度を下げると、対応点の幾何的信頼性が落ちる可能性を示しています。したがって、共有する情報量だけでなく、共有する頻度も研究対象にできます。

### 4.3 特徴点選択方法で精度が変わる

同じ特徴点数だけ送る場合でも、どの特徴点を選ぶかでinlier数が変わりました。

100特徴点だけ送る場合:

| group | strategy | avg fundamental inliers | compact/JPEG |
| --- | --- | ---: | ---: |
| structured | top_response | 52.810 | 0.8% |
| structured | grid | 43.668 | 0.8% |
| structured | random | 11.086 | 0.8% |
| unstructured_like | top_response | 43.213 | 0.4% |
| unstructured_like | grid | 35.568 | 0.4% |
| unstructured_like | random | 9.051 | 0.4% |

500特徴点だけ送る場合:

| group | strategy | avg fundamental inliers | compact/JPEG |
| --- | --- | ---: | ---: |
| structured | top_response | 252.230 | 3.9% |
| structured | grid | 224.255 | 3.9% |
| structured | random | 101.048 | 3.9% |
| unstructured_like | top_response | 216.424 | 2.0% |
| unstructured_like | grid | 187.141 | 2.0% |
| unstructured_like | random | 75.239 | 2.0% |

現時点では、responseが高い特徴点を優先する`top_response`が最も良く、画像全体に分散するように選ぶ`grid`も比較的近い性能でした。ランダム選択は大きく劣りました。今後は、`top_response`と`grid`を組み合わせ、強い特徴点を選びつつ空間分布も保つ方式を試す価値があります。

## 5. 論文・既存手法との関係

### 5.1 ORB-SLAM3との関係

ORB-SLAM3は、Visual、Visual-Inertial、Multi-Mapに対応した代表的なSLAMシステムです。本研究では、SLAM本体を一から作るのではなく、まずORB-SLAM3を単体SLAMの基準実装として利用します。

本研究でORB-SLAM3を使う理由は、Frame、KeyFrame、MapPoint、Camera Pose、BoW vectorなど、通信対象として検討したい内部情報が明確に存在するためです。ORB-SLAM3を安定して実行し、KeyFrameTrajectory、実行ログ、ATEを保存できるようにすることで、通信方式を変えたときの比較基盤にできます。

### 5.2 ORB特徴量・DBoW2との関係

ORB特徴量は、特徴点とバイナリdescriptorから構成されます。descriptorがバイナリで小さいため、通信量を抑えたSLAMや場所認識に向いています。本研究では、ORB descriptorを1特徴点あたり32 bytesとして扱い、画像全体を送る場合との通信量差を評価しています。

DBoW2のBag-of-Binary-Wordsは、画像全体ではなくBoW vectorによって場所認識を行う考え方です。本研究でORB-SLAM3内部のBoW vectorを確認対象に入れているのは、ロボット間で「画像」ではなく「場所認識に必要な要約情報」を共有できる可能性があるためです。

### 5.3 協調SLAM研究との関係

CCM-SLAMのような協調SLAM研究では、複数カメラや複数ロボットの地図を統合する枠組みが扱われています。一方、本研究では最初から完全な協調SLAMシステムを作るのではなく、協調SLAMで共有される情報を分解し、画像、キーフレーム、特徴点、記述子、姿勢、BoW、MapPointのどれを送るべきかを通信量と精度の観点から評価します。

また、通信効率に注目したVisual SLAM研究では、分散環境で必要な特徴情報だけを共有する方向性が提案されています。本研究も同じ問題意識を持ちますが、まずは公開データセットとORB-SLAM3を使い、通信対象を変えた場合の通信量、軌跡精度、実行時間を再現可能に比較する点に重点を置きます。

### 5.4 EuRoCとATE評価との関係

EuRoC MAV datasetは、Visual SLAMやVisual-Inertial SLAMの評価で広く使われる公開データセットです。ground truthがあるため、ORB-SLAM3の推定軌跡と比較してATE RMSEを計算できます。

単眼SLAMではスケールが不定になりやすいため、現在の評価スクリプトではSim(3)アラインメントを行ってからATE RMSEを計算します。これにより、同じ条件で再実行したときの精度やばらつきを比較できます。

## 6. Jetsonなしで今後進められること

Jetsonがなくても、公開データセットとPC実験で次の内容は進められます。

### 6.1 公開データセットで単体SLAM基準を作る

EuRoCの`MH_01_easy`や`V1_01_easy`を使い、ORB-SLAM3を安定して実行します。確認項目は、停止せず最後まで動くこと、`KeyFrameTrajectory.txt`を保存できること、`run.log`を保存できること、ATE RMSEを計算できること、再実行時におおむね同じ結果になることです。

この段階で、軌跡図、ATE、実行時間を保存できれば、研究の基準実験として説明できます。

### 6.2 共有方式を模擬して通信量と精度を比較する

公開データセット上で、次の共有方式を模擬できます。

- 画像全体を送る場合
- キーフレーム画像だけを送る場合
- ORB keypointとdescriptorを送る場合
- descriptorだけを送る場合
- Camera Poseとkeyframe metadataを送る場合
- BoW vectorだけ、またはBoW vectorと少数descriptorを送る場合

この比較では、各方式の通信量をbytes単位で計算し、自己位置推定精度をATE RMSEやRPE、追跡成功率、キーフレーム数、実行時間で評価できます。

### 6.3 帯域制約をソフトウェア的に再現する

実際の無線通信を使わなくても、PC上で「1秒あたり送れるbytes数」を制限し、送信できる特徴点数やキーフレーム数を制限できます。例えば、10KB/s、50KB/s、100KB/s、500KB/sのような条件を設定し、どの共有方式がどの帯域で破綻しにくいかを調べられます。

この実験は、Jetson実機の前に研究仮説を絞るために有効です。

## 7. Jetsonで確認すべきこと

Jetsonが再び使えるようになったら、PCや公開データセットでは分からない実機制約を確認します。

- USBカメラまたはCSIカメラで安定してフレーム取得できるか
- 実機カメラのキャリブレーション値でORB-SLAM3が動くか
- ORB特徴抽出とSLAM追跡が実時間で動くか
- CPU/GPU使用率、メモリ使用量、発熱、消費電力は許容範囲か
- フレーム保存、ログ保存、軌跡保存が長時間動作で破綻しないか
- 実際の通信経路で、特徴量共有が画像共有より有利か

Jetsonでの主な目的は、アルゴリズムの正しさそのものよりも、実機制約下で動くかを確認することです。アルゴリズム比較は、まずPCと公開データセットで進める方が効率的です。

## 8. 今後の実験計画

### Step 1: EuRoCでORB-SLAM3を安定実行

`MH_01_easy`を最初の対象にして、ORB-SLAM3の実行ログ、KeyFrameTrajectory、ATE RMSE、実行時間を保存します。これにより、研究全体の基準となる単体SLAM性能を作ります。

### Step 2: キーフレーム単位の通信量を測る

ORB-SLAM3内部またはキーフレーム時刻に対応する画像から、1キーフレームあたりの画像サイズ、特徴点数、descriptorサイズ、poseサイズ、BoWサイズを記録します。

これにより、「画像を送る場合」と「特徴量を送る場合」の通信量差を、自分の環境で説明できます。

### Step 3: 共有情報を制限した評価

特徴点数、descriptor数、キーフレーム頻度を制限し、通信量を減らしたときにATEや追跡成功率がどう変化するかを評価します。

### Step 4: 特徴点選択方法の改良

現時点では`top_response`が最も良い傾向ですが、非構造環境では空間的な偏りも問題になる可能性があります。そのため、`top_response`と`grid`を組み合わせたハイブリッド選択を実装し、通信量を固定した状態でinlier数やATEを比較します。

### Step 5: Jetson実機評価

PCと公開データセットで絞った方式をJetsonに持ち込みます。実機では、実行時間、フレームレート、CPU/GPU負荷、保存ログ、実通信量を中心に評価します。

## 9. 先生への説明で使える要約

現在はJetson実機での本格実験には入れていませんが、研究の中心である「何を通信すればよいか」を調べるための基盤を作っています。具体的には、ORB特徴量を使って、画像全体を送る場合と特徴点・記述子を送る場合の通信量を比較し、さらにRANSACによる幾何的inlier数を使って、自己位置推定に使えそうな対応点がどの程度残るかを評価しています。

PC上の動画では、1000特徴点を送る場合でも、特徴量パケットはJPEG画像の約3.85%から7.34%程度で済む傾向がありました。一方で、フレーム間隔が広がると幾何的inlier数が大きく減るため、通信量だけでなく、送信頻度や特徴点選択方法も重要であることが分かりました。

今後は、EuRoCのような公開データセットでORB-SLAM3を安定して実行し、ATE RMSE、軌跡図、実行時間、キーフレーム単位の通信量を保存します。これにより、Jetsonが使えない期間でも、通信帯域制約下の協調Visual SLAMを再現し、画像、キーフレーム、特徴点、記述子の共有方式による通信量と自己位置推定精度の違いを評価できます。Jetsonでは、その後に実時間性や実機通信、カメラ条件を検証する予定です。

## 10. 参考文献・参考実装

- Campos et al., "ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM", arXiv: https://arxiv.org/abs/2007.11898
- ORB-SLAM3 official repository: https://github.com/UZ-SLAMLab/ORB_SLAM3
- Rublee et al., "ORB: An efficient alternative to SIFT or SURF", IEEE ICCV 2011: https://ieeexplore.ieee.org/document/6126544
- Galvez-Lopez and Tardos, "Bags of Binary Words for Fast Place Recognition in Image Sequences", IEEE Transactions on Robotics 2012: https://ieeexplore.ieee.org/document/6202705
- Burri et al., "The EuRoC micro aerial vehicle datasets", IJRR 2016: https://projects.asl.ethz.ch/datasets/
- Sturm et al., "A Benchmark for the Evaluation of RGB-D SLAM Systems", IROS 2012: https://vision.in.tum.de/data/datasets/rgbd-dataset
- Schmuck and Chli, "CCM-SLAM: Robust and efficient centralized collaborative monocular simultaneous localization and mapping for robotic teams", Journal of Field Robotics 2019: https://onlinelibrary.wiley.com/doi/10.1002/rob.21854
- Cieslewski et al., "Data-Efficient Decentralized Visual SLAM", ICRA 2018: https://arxiv.org/abs/1710.05772
