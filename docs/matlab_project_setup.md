# MATLAB Project Setup

この既存Gitリポジトリを、MATLAB Projectとして初期化する手順です。新しいリポジトリは作成しません。

## MATLAB Onlineでの初期化

1. MATLAB Onlineで`my-research`リポジトリを開きます。
2. Filesパネルでリポジトリのルートを現在のフォルダにします。
3. Command Windowで次を実行します。

   ```matlab
   setup_matlab_project
   ```

4. Projectパネルが開き、プロジェクト名が`my-research`になっていることを確認します。
5. Project SettingsのProject Pathで、次のフォルダが登録されていることを確認します。

   - `configs/matlab`
   - `experiments`
   - `simulink`
   - `src/communication`
   - `src/evaluation`
   - `src/features`
   - `src/slam`

6. Source Controlパネルで、既存Gitリポジトリが認識されていることを確認します。

## MATLABが生成するファイル

初期化すると、ルートの`.prj`ファイルと`resources/project/`以下のProject定義ファイルが生成されます。これらはProject名、登録ファイル、検索パスなどを保持するため、内容を確認したうえでGitへコミットします。

Project定義ファイルはMATLABが管理するため、手作業で編集しません。

## データと結果の扱い

初期化スクリプトは、巨大なローカルデータをProjectへ一括登録しません。

- `data/euroc/`、`data/interim/`などのデータ本体は登録対象外です。
- `results/`の再生成可能な大きな出力も登録対象外です。
- `data/README.md`、`data/metadata/`、結果ディレクトリの案内READMEは登録します。

実験コードからデータを読み込むことは可能であり、Projectへの登録とデータアクセスは別のものです。

## GUIだけで作成する場合

スクリプトを使わない場合は、MATLABのHomeタブから`New > Project`を選択し、既存の`my-research`フォルダを指定します。その後、Project Settingsで上記のProject Pathを追加します。
