# DirStringSearch (Windows用)
ディレクトリを指定して、PowerShellの  
`Get-ChildItem <dir> -Recurse -Filter *.* | Select-String -Pattern "<文字列>"`  
相当の検索をGUIで実行するツール。UTF-8日本語OK。ログは `./log` に出力。

## 使い方（Pythonで直接起動）
1. WindowsでPython3.10+を用意
2. `dirgrep_app.py` をダブルクリック、起動しない場合は `py dirgrep_app.py`
3. 「ディレクトリ」を選択、「検索パターン」を入力して「検索」。  
   - 「正規表現」: PowerShellの `Select-String` と同様に正規表現で検索  
   - 「大文字小文字を区別」: ONで case-sensitive
   - ダブルクリックでファイルを既定アプリで開く
   - CSV出力ボタンで結果保存

## EXE化（PyInstaller）
1. `pip install pyinstaller`
2. 同じフォルダで実行:  
   ```bat
   pyinstaller --onefile --noconsole --name DirStringSearch dirgrep_app.py
   ```
3. `dist/DirStringSearch.exe` が生成されます。`log` フォルダはEXEと同じ階層に自動作成。

## ログ
- `./log/YYYYMMDD.log` に、検索開始/終了、スキャンしたファイル数、ヒット件数、エラー等を記録。

## 備考
- 既定で一部のバイナリ拡張子をスキップします（.exe/.dll/.zip など）。
- 読み込みエンコーディングは `utf-8 → utf-8-sig → cp932 → utf-16 → iso-8859-1` を順に試行。  
  それでも無理な場合は無視して続行（PowerShell相当の挙動を意識）。
