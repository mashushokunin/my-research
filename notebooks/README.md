# Notebooks

試行錯誤、可視化、簡易分析のためのJupyter Notebookを置くディレクトリです。

Notebook内で重要な処理が固まったら、再利用できるように `src/` または `scripts/` に移します。

## 動画ごとの確認

`videos/` には、動画ごとの確認用Notebookがあります。まず索引用Notebookを開いて、対象の動画へ移動します。

```bash
jupyter lab notebooks/videos/00_video_index.ipynb
```

各Notebookでは、代表フレーム、ORB特徴点、隣接フレームのマッチング、保存済み特徴量ファイル、歪み補正の試行を確認できます。

動画を追加したりフレームを作り直した場合は、以下でNotebookを再生成します。

```bash
python scripts/create_video_notebooks.py
```
