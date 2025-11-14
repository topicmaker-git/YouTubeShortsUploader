# YouTube Shorts Uploader

YouTube Data API v3を使用してShorts動画を自動アップロードするPythonツールです。

## 機能

- YouTube Shorts動画の自動アップロード
- バッチアップロード（複数動画の一括アップロード）
- 動画の事前検証（アスペクト比、解像度、動画長のチェック）
- APIクォータ管理
- アップロード履歴の保存
- エラーハンドリングと再試行
- **再生リスト管理**（自動作成・動画追加）
- **公開日時のスケジュール設定**

## 必要要件

- Python 3.7以上
- Google Cloud Console プロジェクト
- YouTube Data API v3 の有効化
- OAuth 2.0 クライアント認証情報
- （オプション）ffmpeg（動画検証機能を使用する場合）

## インストール

### クイックスタート

**Windows:**
```batch
setup.bat
```

**Linux/Mac:**
```bash
./setup.sh
```

セットアップスクリプトは以下を自動的に実行します:
- 仮想環境の作成
- 依存パッケージのインストール
- 必要なディレクトリの作成
- client_secretファイルの確認
- ffmpegのチェックとインストール（オプション）

ffmpegがインストールされていない場合:
- **Windows**: winget（Windows 10/11標準）を優先的に使用し、自動インストールを選択可能
- **Linux**: apt-getまたはdnfを使用した自動インストールを選択可能
- **macOS**: Homebrewを使用した自動インストールを選択可能

### ffmpegの手動インストール

**Windows（推奨順）:**

1. **winget経由（Windows 10/11標準、最も簡単）:**
```batch
winget install -e --id Gyan.FFmpeg
```
**注意:** インストール後、新しいターミナルを開いてPATH変更を反映させてください。

2. **ポータブル版（PATH設定不要）:**
```batch
install_ffmpeg_portable.bat
```

3. **Chocolatey経由:**
```batch
choco install ffmpeg
```

**手動インストール:**
- Windows: https://github.com/BtbN/FFmpeg-Builds/releases
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- macOS: `brew install ffmpeg`

ffmpegがない場合でも`--skip-validation`オプションでアップロード可能です。

### Google Cloud Consoleの設定（事前準備）

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新規プロジェクトを作成
3. YouTube Data API v3を有効化
4. OAuth 2.0クライアントIDを作成（デスクトップアプリ）
5. 認証情報JSONファイルをダウンロード
6. ダウンロードしたファイルをプロジェクトのルートディレクトリに配置

### OAuth同意画面の設定

必要なスコープ:
- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube`

## 使い方

### 認証

初回実行時、またはトークンの期限が切れた場合は認証が必要です。

**Windows:**
```batch
run.bat auth --show-info
```

**Linux/Mac:**
```bash
./run.sh auth --show-info
```

または、仮想環境を有効化してから実行:

**Windows:**
```batch
venv\Scripts\activate
python main.py auth --show-info
```

**Linux/Mac:**
```bash
source venv/bin/activate
python main.py auth --show-info
```

認証が成功すると、`token.json`ファイルが作成され、次回以降は自動的に認証されます。

### 単一動画のアップロード

**Windows:**
```batch
run.bat upload shorts_videos\video.mp4 -t "Title" -d "Description"
```

**Linux/Mac:**
```bash
./run.sh upload shorts_videos/video.mp4 -t "Title" -d "Description"
```

オプション:
- `-t, --title`: 動画のタイトル（必須）
- `-d, --description`: 動画の説明文
- `--tags`: タグ（カンマ区切り）
- `-c, --category`: カテゴリID（デフォルト: 22）
- `-p, --privacy`: 公開設定（public/private/unlisted、デフォルト: public）
- `--playlist`: 追加する再生リスト名（事前にYouTube Studioで作成が必要）
- `--publish-at`: 公開予定日時（**日本時間**で指定: "2025-11-20 19:00:00" または "2025-11-20 19:00"）
- `--skip-validation`: 動画検証をスキップ
- `--force`: 検証エラーを無視して強制アップロード

例:

```bash
# 基本的なアップロード
python main.py upload shorts_videos/sample.mp4 \
  -t "テスト動画" \
  -d "これはテスト動画です" \
  --tags "Shorts,テスト,Python" \
  -p private

# 再生リストに追加
python main.py upload shorts_videos/sample.mp4 \
  -t "テスト動画" \
  --playlist "マイショーツコレクション"

# スケジュール公開（2025年11月20日 19:00 日本時間）
python main.py upload shorts_videos/sample.mp4 \
  -t "スケジュール動画" \
  --publish-at "2025-11-20 19:00:00"

# 再生リスト＋スケジュール公開
python main.py upload shorts_videos/sample.mp4 \
  -t "スケジュール動画" \
  --playlist "マイショーツコレクション" \
  --publish-at "2025-11-20 19:00"
```

### バッチアップロード

ディレクトリ内の動画を一括アップロード:

```bash
python main.py batch -d shorts_videos -i 30 --save-history
```

CSVファイルから一括アップロード:

```bash
python main.py batch -c upload_list.csv --save-history
```

CSVファイルの形式:
```csv
file,title,description,tags,category_id,privacy_status,playlist_name,publish_at
shorts_videos/video1.mp4,タイトル1,説明文1,"tag1,tag2",22,public,マイショーツ,
shorts_videos/video2.mp4,タイトル2,説明文2,"tag3,tag4",28,public,マイショーツ,2025-11-20 19:00:00
shorts_videos/video3.mp4,タイトル3,説明文3,"tag5,tag6",22,private,テスト用,2025-11-21 12:30
```

**新しいCSVカラムの説明:**
- `playlist_name`: 動画を追加する再生リスト名（空欄可、事前にYouTube Studioで作成が必要）
- `publish_at`: 公開予定日時（**日本時間**で指定、空欄の場合は即座に公開）
  - 形式: `yyyy-mm-dd hh:mm:ss` または `yyyy-mm-dd hh:mm`
  - 例: `2025-11-20 19:00:00`（2025年11月20日 19:00 日本時間）
  - 例: `2025-11-21 12:30`（秒は省略可能）

オプション:
- `-d, --directory`: 動画が格納されているディレクトリ
- `-c, --csv-file`: メタデータCSVファイル
- `--pattern`: ファイルパターン（デフォルト: *.mp4）
- `-i, --interval`: アップロード間隔（分、デフォルト: 30）
- `--save-history`: アップロード履歴を保存

### 再生リスト管理

再生リストの一覧表示や動画の追加が可能です。

```bash
# アップロード時に再生リストに追加（存在しない場合は自動作成）
python main.py upload shorts_videos/sample.mp4 \
  -t "タイトル" \
  --playlist "マイショーツコレクション"
```

**再生リストの仕組み:**
- 再生リスト名を指定すると、既存の再生リストから名前で検索
- **見つからない場合は警告を表示し、再生リストなしでアップロード**
- タイポによる誤った再生リスト作成を防ぎます
- 作成された再生リストIDはキャッシュされ、同じ名前の場合は再利用
- CSVファイルで複数の動画を同じ再生リストに追加することも可能

**注意:** 再生リストは自動作成されません。事前にYouTube Studioで作成しておいてください。

### スケジュール実行（自動アップロード）

**Windowsタスクスケジューラーで定期実行**し、数十本の動画を1日数本ずつ自動アップロードできます。

```bash
# 手動でテスト実行（先頭5件をアップロード）
python main.py scheduled -c upload_list.csv -n 5
```

**動作:**
1. `upload_list.csv`から先頭N件（デフォルト: 5件）を読み込み
2. アップロードを実行
3. 成功した行をCSVから削除
4. 実行結果とログを`logs/scheduled_upload_YYYYMMDD_HHMMSS.log`に保存
5. CSVが空になるまで繰り返し（タスクスケジューラーで毎日実行）

**セットアップ手順:**

1. `upload_list.csv`に全動画の情報を記載
2. `scheduled_upload.bat`をダブルクリックしてテスト実行
3. Windowsタスクスケジューラーに登録:
   - タスクスケジューラーを開く
   - 「基本タスクの作成」を選択
   - トリガー: 毎日（例: 午前10時）
   - 操作: プログラムの開始
   - プログラム/スクリプト: `scheduled_upload.bat`の絶対パス
   - 開始: プロジェクトのルートディレクトリ

**オプション:**
- `-c, --csv-file`: CSVファイルのパス（デフォルト: upload_list.csv）
- `-n, --max-uploads`: 1回の実行で処理する件数（デフォルト: 5）
- `--log-file`: ログファイルのパス（指定しない場合は自動生成）

**利点:**
- 手間を大幅に削減（数十本の動画を自動処理）
- APIクォータを分散（1日5本なら余裕で制限内）
- エラー時も次回の実行で自動リトライ
- 実行履歴がログに残る

### 公開日時のスケジュール設定

将来の日時を指定して動画を予約公開できます。

```bash
# 2025年11月20日 19:00（日本時間）に公開
python main.py upload shorts_videos/sample.mp4 \
  -t "スケジュール動画" \
  --publish-at "2025-11-20 19:00:00"

# 秒は省略可能
python main.py upload shorts_videos/sample.mp4 \
  -t "スケジュール動画" \
  --publish-at "2025-11-20 19:00"
```

**注意事項:**
- スケジュール公開を設定した動画は、一旦`private`としてアップロードされ、指定日時に自動的に公開されます
- **日本時間（JST）**で指定してください。自動的にUTCに変換されます
- 形式: `yyyy-mm-dd hh:mm:ss` または `yyyy-mm-dd hh:mm`（秒は省略可）
- 例: `2025-11-20 19:00:00` → YouTube APIには `2025-11-20T10:00:00Z` (UTC) として送信されます

### 動画の検証

単一ファイルの検証:

```bash
python main.py validate shorts_videos/sample.mp4
```

ディレクトリ内の全ファイルを検証:

```bash
python main.py validate -d shorts_videos
```

### クォータ管理

現在のクォータ状態を確認:

```bash
python main.py quota
```

クォータをリセット:

```bash
python main.py quota --reset
```

## YouTube Shortsの仕様

| 項目 | 仕様 |
|------|------|
| アスペクト比 | 9:16（推奨）または 1:1 |
| 解像度 | 最小720p / 推奨1080p（1920×1080px） |
| 動画の長さ | 15秒〜180秒（3分） |
| ファイルサイズ | 最大128GB（API経由） |
| ファイル形式 | MP4、MOV |

**注意:**
- 解像度チェックは警告のみで、どの解像度でもアップロード可能です
- 720p未満の動画は警告が表示されます
- 1080p以上が最良の画質で推奨されます
- YouTubeは低解像度の動画も受け入れますが、画質は低下します

### Shortsとして認識される条件

1. タイトルまたは説明文に `#Shorts` ハッシュタグを含める
2. 動画が60秒以内で縦型（9:16）または正方形（1:1）のアスペクト比
3. YouTube Studioから「Shorts」として直接アップロード

このツールでは、自動的に `#Shorts` タグがタイトルと説明文に追加されます。

## APIクォータについて

YouTube Data API v3は1日あたり10,000ユニットのクォータ制限があります。

主な操作のコスト:
- 動画アップロード（videos.insert）: 1,600ユニット
- 動画情報取得（videos.list）: 1ユニット
- チャンネル情報取得（channels.list）: 1ユニット

1日にアップロードできる動画数: 約6本（10,000 ÷ 1,600 = 6.25）

クォータは太平洋時間の午前0時（日本時間の午後5時）にリセットされます。

## カテゴリID一覧

| ID | カテゴリ |
|----|---------|
| 1 | Film & Animation |
| 2 | Autos & Vehicles |
| 10 | Music |
| 15 | Pets & Animals |
| 17 | Sports |
| 19 | Travel & Events |
| 20 | Gaming |
| 22 | People & Blogs |
| 23 | Comedy |
| 24 | Entertainment |
| 25 | News & Politics |
| 26 | Howto & Style |
| 27 | Education |
| 28 | Science & Technology |
| 29 | Nonprofits & Activism |

## プロジェクト構造

```
YouTubeShortsUploader/
├── src/
│   ├── __init__.py
│   ├── auth.py              # 認証モジュール
│   ├── uploader.py          # アップロードモジュール
│   ├── batch_uploader.py    # バッチアップロードモジュール
│   ├── validator.py         # 動画検証モジュール
│   ├── quota_manager.py     # クォータ管理モジュール
│   └── playlist_manager.py  # 再生リスト管理モジュール
├── shorts_videos/           # 動画ファイル格納ディレクトリ
├── logs/                    # ログとアップロード履歴
├── main.py                  # メインスクリプト
├── requirements.txt         # 依存パッケージ
├── .gitignore
└── README.md
```

## トラブルシューティング

### 認証エラーが発生する

1. `client_secret.json` ファイルがプロジェクトルートに配置されているか確認
2. Google Cloud ConsoleでOAuth 2.0クライアントIDが正しく設定されているか確認
3. 必要なスコープが追加されているか確認
4. `token.json` ファイルを削除して再認証を試す

### クォータ超過エラー

```
quotaExceeded: APIクォータを超過しました
```

YouTube Data API v3の1日あたりのクォータ（10,000ユニット）を超過しています。
24時間後に再試行するか、Google Cloud Consoleでクォータの増加をリクエストしてください。

### 動画がShortsとして認識されない

1. 動画のアスペクト比が9:16または1:1であることを確認
2. 動画の長さが180秒以内であることを確認
3. タイトルまたは説明文に `#Shorts` タグが含まれていることを確認

### ffprobeが見つからない

動画検証機能を使用するには、ffmpegのインストールが必要です。

Ubuntu/Debian:
```bash
sudo apt-get install ffmpeg
```

macOS:
```bash
brew install ffmpeg
```

Windows:
[ffmpeg公式サイト](https://ffmpeg.org/download.html)からダウンロードしてインストール

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 参考資料

- [YouTube Data API v3 ドキュメント](https://developers.google.com/youtube/v3)
- [YouTube Shorts 公式ヘルプ](https://support.google.com/youtube/answer/10059070)
- [API クォータについて](https://developers.google.com/youtube/v3/getting-started#quota)

## 自動アップロードの実用例

### シナリオ: 30本の動画を毎日5本ずつアップロード

1. **準備:**
   ```bash
   # 30本の動画情報をCSVに記載
   # upload_list.csv に30行のデータを用意
   ```

2. **テスト実行:**
   ```bash
   # 先頭5件をテストアップロード
   scheduled_upload.bat
   ```

3. **タスクスケジューラーに登録:**
   - 毎日午前10時に実行
   - `scheduled_upload.bat`を指定

4. **自動実行:**
   - 1日目: 1-5本目がアップロード、CSVに25行残る
   - 2日目: 6-10本目がアップロード、CSVに20行残る
   - ...
   - 6日目: 26-30本目がアップロード、CSVが空になる

5. **結果確認:**
   ```
   logs/
   ├── scheduled_upload_20251114_100000.log  # 1日目
   ├── scheduled_upload_20251115_100000.log  # 2日目
   └── ...
   ```

**APIクォータ計算:**
- 1回のアップロード: 1,600ユニット
- 5本/日: 8,000ユニット（制限10,000ユニット内）
- 余裕あり！

## 注意事項

- このツールを使用する際は、YouTubeの利用規約とコミュニティガイドラインを遵守してください
- APIクォータの制限に注意してください（1日10,000ユニット）
- スケジュール実行では1日5本程度が安全です
- 動画のアップロードには時間がかかる場合があります
- エラーが発生した行も削除されますが、ログに記録されます
- 失敗した動画は手動でアップロードするか、CSVに再度追加してください
