# CLAUDE.md - 開発者向けドキュメント

このファイルは、将来のバグ修正や機能拡張のために、プロジェクトの概要と開発時の重要な判断を記録したものです。

## プロジェクト概要

### 目的
YouTube Data API v3を使用してYouTube Shorts動画を自動アップロードするPythonツール。
**最大の存在意義**: 数十本の動画を量産し、YouTube Studioへの手動アップロードの手間を大幅に削減すること。

### 主な機能
1. **単一動画アップロード**: 1本の動画を即座にアップロード
2. **バッチアップロード**: 複数動画を一括処理（CSVまたはディレクトリから）
3. **スケジュール実行**: Windowsタスクスケジューラーで定期自動アップロード（1日N本ずつ）
4. **動画検証**: アスペクト比・解像度・動画長のチェック（警告のみ、ブロックしない）
5. **再生リスト管理**: 既存再生リストへの動画追加（自動作成はしない）
6. **公開スケジュール**: 日本時間で指定した日時に自動公開
7. **APIクォータ管理**: 1日10,000ユニット制限の追跡
8. **詳細ログ**: 全実行結果を日時付きログファイルに保存

## アーキテクチャ

### モジュール構成

```
src/
├── auth.py              # OAuth 2.0認証、トークン管理
├── uploader.py          # 単一動画アップロード、日時変換
├── batch_uploader.py    # バッチ処理、スケジュール実行、CSV管理
├── playlist_manager.py  # 再生リスト検索・追加
├── validator.py         # 動画検証（ffprobe使用）
└── quota_manager.py     # クォータ追跡
```

### データフロー

**スケジュール実行（主要ユースケース）:**
```
1. scheduled_upload.bat (Windowsタスクスケジューラー)
   ↓
2. main.py scheduled コマンド
   ↓
3. ShortsBatchUploader.upload_from_csv_scheduled()
   ↓
4. CSVから先頭N件を読み込み
   ↓
5. 各動画に対して:
   - PlaylistManager.get_playlist() で再生リスト検索
   - convert_jst_to_utc_iso8601() で日時変換
   - upload_with_retry() でアップロード
   ↓
6. 成功した行をCSVから削除（バックアップ作成）
   ↓
7. ログファイルに詳細を記録
```

## 重要な設計判断と経緯

### 1. 解像度チェックは警告のみ

**経緯**:
- 当初は1080p最低要件でエラーブロック
- ユーザーの480x872動画が拒否される
- `--force`フラグが必須になり実用的でない

**判断**:
- 解像度チェックを警告のみに変更
- YouTubeは低解像度も受け入れるため、ユーザーの判断に委ねる
- アスペクト比・動画長・ファイルサイズのみ必須チェック

**該当コード**: `src/validator.py:174-187`

### 2. 再生リストは自動作成しない

**経緯**:
- 当初は見つからない場合に自動作成する設計
- ユーザー指摘: タイポで意図しない再生リストが量産される

**判断**:
- `get_or_create_playlist()` は残すが、主要機能では使わない
- `get_playlist()` を新設し、見つからない場合はNoneを返す
- 警告を表示し、再生リストなしでアップロード継続
- 事前にYouTube Studioで作成することを推奨

**該当コード**: `src/playlist_manager.py:22-76`

### 3. 日本時間（JST）対応

**経緯**:
- 当初はISO 8601形式（UTC）で指定
- ユーザー要望: `yyyy-mm-dd hh:mm:ss`形式で日本時間入力したい

**判断**:
- `convert_jst_to_utc_iso8601()` 関数を実装
- 入力: `2025-11-20 19:00:00` (JST)
- 変換: `2025-11-20T10:00:00Z` (UTC)
- 秒省略も対応: `2025-11-20 19:00`

**該当コード**: `src/uploader.py:12-58`

### 4. CSV処理後の行削除

**経緯**:
- スケジュール実行で「進捗管理」が必要
- 何度も同じ動画をアップロードしないようにする

**判断**:
- 処理した行（成功・失敗問わず）をCSVから削除
- 削除前に`.backup`ファイルを自動作成
- CSVが空になった時点で全アップロード完了
- 失敗した動画はログから確認して手動対応

**該当コード**: `src/batch_uploader.py:400-417`

### 5. Windows優先設計

**経緯**:
- 主要ターゲットユーザーはWindows環境
- ffmpegインストールの障壁を下げる

**判断**:
- `setup.bat`でwinget（Windows標準）を優先
- ポータブル版ffmpegにも対応（PATH不要）
- `scheduled_upload.bat`でタスクスケジューラー対応
- Linux/macOS用のスクリプトも提供（run.sh, setup.sh）

**該当ファイル**: `setup.bat`, `scheduled_upload.bat`

## 技術的な制約と注意点

### API制限
- **1日のクォータ**: 10,000ユニット
- **1回のアップロード**: 1,600ユニット
- **実質制限**: 1日6本まで
- **推奨**: スケジュール実行で1日5本（余裕を持たせる）
- **リセット時刻**: 太平洋時間午前0時（日本時間17時）

### YouTube Shorts要件
- **アスペクト比**: 9:16（縦型）または 1:1（正方形）【必須】
- **動画長**: 最大180秒（3分）【必須】
- **解像度**: 720p以上推奨、低解像度でも可【警告のみ】
- **ファイルサイズ**: 最大128GB【必須】
- **#Shortsタグ**: 自動付与

### スケジュール公開の仕様
- スケジュール設定時、動画は一旦`private`でアップロード
- 指定日時にYouTubeが自動的に公開
- `privacy_status='public'`でも`publish_at`があれば上書き

## ディレクトリ構造

```
YouTubeShortsUploader/
├── src/                    # ソースコード
├── shorts_videos/          # 動画ファイル格納（.gitkeep）
├── logs/                   # ログファイル（.gitkeep、ファイル自体はgit除外）
├── main.py                 # CLIエントリーポイント
├── setup.bat/sh            # セットアップスクリプト
├── run.bat/sh              # 実行ラッパー
├── scheduled_upload.bat    # タスクスケジューラー用
├── upload_list.csv.example # CSVサンプル
├── requirements.txt        # 依存パッケージ
├── README.md               # ユーザー向けドキュメント
├── QUICK_START.md          # クイックスタートガイド
└── CLAUDE.md               # このファイル（開発者向け）
```

## 重要なファイルと役割

### client_secret.json（gitignore）
- Google Cloud ConsoleからダウンロードしたOAuth認証情報
- ユーザーが自分で用意する必要がある
- **絶対にコミットしない**

### token.json（gitignore）
- OAuth認証後に自動生成されるアクセストークン
- 有効期限あり、期限切れ時は自動リフレッシュ
- **絶対にコミットしない**

### upload_list.csv（gitignore）
- ユーザーが作成するアップロード対象リスト
- スケジュール実行で先頭から処理され、行が削除されていく
- `.example`ファイルをコピーして使用

### quota_state.json（gitignore）
- APIクォータの使用状況を記録
- 日次でリセット

## トラブルシューティング

### よくある問題と解決方法

**1. 再生リストが見つからない**
- 現象: 警告が表示され、再生リストなしでアップロード
- 原因: タイポまたは再生リストが未作成
- 解決: YouTube Studioで再生リストを作成、名前を正確に記載

**2. ffprobeが見つからない**
- 現象: 動画検証ができない
- 原因: ffmpegが未インストール
- 解決: `setup.bat`を再実行、またはwingetで手動インストール
- 回避: `--skip-validation`オプションで検証をスキップ

**3. 認証エラー**
- 現象: `client_secret.json not found`
- 原因: Google Cloud Consoleで認証情報未ダウンロード
- 解決: README.mdの「Google Cloud Consoleの設定」を参照

**4. クォータ超過**
- 現象: `quotaExceeded`エラー
- 原因: 1日10,000ユニット制限に到達
- 解決: 24時間待機（日本時間17時にリセット）

**5. スケジュール実行が動かない**
- 現象: タスクスケジューラーで実行されない
- 原因: パスが相対パスになっている
- 解決: `scheduled_upload.bat`の絶対パスを指定、開始ディレクトリも設定

## 拡張のためのヒント

### 新しい機能を追加する場合

**1. サムネイル設定機能**
- `uploader.py`に`set_thumbnail()`メソッド追加
- YouTube APIの`thumbnails.set`エンドポイント使用
- CSVに`thumbnail`カラム追加

**2. 字幕アップロード**
- `uploader.py`に`upload_caption()`メソッド追加
- YouTube APIの`captions.insert`エンドポイント使用
- CSVに`caption_file`カラム追加

**3. 他言語対応**
- 現在は日本語メッセージ
- `messages.py`などでメッセージを分離
- 環境変数で言語切り替え

### テスト方法

**単体テスト**:
```bash
# 認証テスト
python -m src.auth

# 検証テスト
python -m src.validator

# 再生リストテスト
python -m src.playlist_manager
```

**統合テスト**:
```bash
# private設定でテストアップロード
python main.py upload test.mp4 -t "Test" -p private

# スケジュール実行テスト（CSVに1行だけ）
python main.py scheduled -c test.csv -n 1
```

## バージョン情報

- **初回リリース**: 2025-11-14
- **Python要件**: 3.7以上
- **主要依存**: google-api-python-client, google-auth-oauthlib

## 貢献者

- **初期開発**: Claude Code (Anthropic)
- **プロダクトオーナー**: takahashi@topicmaker.com

## ライセンス

MIT License

---

**最終更新**: 2025-11-14
**メンテナー**: Claude Code
