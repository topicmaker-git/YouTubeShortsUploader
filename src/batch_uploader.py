"""
YouTube Shorts バッチアップロードモジュール
複数の動画を一括でアップロードする機能を提供します。
"""

import os
import time
import csv
import glob
import shutil
import logging
from datetime import datetime, timedelta
from .uploader import upload_with_retry
from .playlist_manager import PlaylistManager


class ShortsBatchUploader:
    """YouTube Shorts バッチアップロードクラス"""

    def __init__(self, youtube_client):
        """
        初期化

        Args:
            youtube_client: YouTube API クライアント
        """
        self.youtube = youtube_client
        self.upload_history = []
        self.playlist_manager = PlaylistManager(youtube_client)

    def schedule_upload(self, video_files, interval_minutes=30, metadata_list=None):
        """
        指定された間隔で動画を予約投稿する

        Args:
            video_files (list): 動画ファイルのリスト
            interval_minutes (int): 投稿間隔（分）
            metadata_list (list): メタデータのリスト（Noneの場合は自動生成）

        Returns:
            list: アップロード結果のリスト
        """
        scheduled_time = datetime.now()
        results = []

        print(f"\n=== バッチアップロード開始 ===")
        print(f"対象動画数: {len(video_files)}")
        print(f"投稿間隔: {interval_minutes}分\n")

        for i, video_file in enumerate(video_files):
            print(f"\n[{i + 1}/{len(video_files)}] {os.path.basename(video_file)}")

            # メタデータを取得または自動生成
            if metadata_list and i < len(metadata_list):
                metadata = metadata_list[i]
            else:
                metadata = self.generate_metadata(video_file)

            # 予約投稿時刻を設定
            metadata['scheduled_time'] = scheduled_time

            # アップロード実行
            result = upload_with_retry(self.youtube, video_file, metadata)

            if result:
                # 履歴に追加
                history_entry = {
                    'file': video_file,
                    'video_id': result['id'],
                    'title': result['title'],
                    'url': result['url'],
                    'uploaded_at': datetime.now().isoformat(),
                    'scheduled_for': scheduled_time.isoformat(),
                    'privacy_status': result['privacy_status']
                }
                self.upload_history.append(history_entry)
                results.append(result)

                print(f"✓ アップロード成功: {result['url']}")
            else:
                print(f"✗ アップロード失敗: {video_file}")

            # 次の投稿時刻を計算
            scheduled_time += timedelta(minutes=interval_minutes)

            # API制限を考慮して待機（最後のファイル以外）
            if i < len(video_files) - 1:
                wait_time = 10
                print(f"\n{wait_time}秒待機してから次の動画をアップロードします...")
                time.sleep(wait_time)

        print(f"\n=== バッチアップロード完了 ===")
        print(f"成功: {len(results)}/{len(video_files)}")

        return results

    def upload_from_directory(self, directory, pattern='*.mp4', **kwargs):
        """
        指定ディレクトリ内の動画ファイルを一括アップロード

        Args:
            directory (str): 動画ファイルが格納されているディレクトリ
            pattern (str): ファイルパターン（デフォルト: '*.mp4'）
            **kwargs: schedule_uploadに渡す追加引数

        Returns:
            list: アップロード結果のリスト
        """
        # ディレクトリ内の動画ファイルを検索
        search_pattern = os.path.join(directory, pattern)
        video_files = sorted(glob.glob(search_pattern))

        if not video_files:
            print(f"警告: {search_pattern} に一致するファイルが見つかりませんでした")
            return []

        print(f"{len(video_files)}個の動画ファイルが見つかりました")
        for i, video_file in enumerate(video_files, 1):
            print(f"  {i}. {os.path.basename(video_file)}")

        return self.schedule_upload(video_files, **kwargs)

    def upload_from_csv(self, csv_file):
        """
        CSVファイルからメタデータを読み込んでアップロード

        CSV形式:
        file,title,description,tags,category_id,privacy_status,playlist_name,publish_at

        Args:
            csv_file (str): CSVファイルのパス

        Returns:
            list: アップロード結果のリスト
        """
        video_files = []
        metadata_list = []

        print(f"CSVファイルを読み込んでいます: {csv_file}")

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    video_files.append(row['file'])

                    # タグをリストに変換
                    tags = []
                    if 'tags' in row and row['tags']:
                        tags = [tag.strip() for tag in row['tags'].split(',')]

                    # 再生リスト名からIDを取得（見つからない場合は警告のみ）
                    playlist_id = None
                    if 'playlist_name' in row and row['playlist_name']:
                        playlist_id = self.playlist_manager.get_playlist(row['playlist_name'])
                        if not playlist_id:
                            print(f"警告: 再生リスト '{row['playlist_name']}' が見つかりません。")
                            print(f"      動画は再生リストなしでアップロードされます。")
                            print(f"      YouTube Studioで後から追加してください。")

                    metadata = {
                        'title': row.get('title', ''),
                        'description': row.get('description', ''),
                        'tags': tags,
                        'category_id': row.get('category_id', '22'),
                        'privacy_status': row.get('privacy_status', 'public'),
                        'playlist_id': playlist_id,
                        'publish_at': row.get('publish_at', None)  # ISO 8601形式: "2025-11-20T10:00:00Z"
                    }
                    metadata_list.append(metadata)

            print(f"{len(video_files)}件のメタデータを読み込みました")
            return self.schedule_upload(video_files, metadata_list=metadata_list)

        except FileNotFoundError:
            print(f"エラー: CSVファイルが見つかりません: {csv_file}")
            return []
        except Exception as e:
            print(f"エラー: CSVファイルの読み込みに失敗しました: {e}")
            return []

    def generate_metadata(self, video_file):
        """
        動画ファイル名からメタデータを自動生成

        Args:
            video_file (str): 動画ファイルのパス

        Returns:
            dict: メタデータ
        """
        filename = os.path.basename(video_file)
        base_name = os.path.splitext(filename)[0]

        return {
            'title': f"{base_name}",
            'description': f"自動アップロードされたShorts動画です。\n投稿日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
            'tags': ['Shorts', '自動投稿'],
            'category_id': '22',
            'privacy_status': 'public'
        }

    def save_history(self, filename='upload_history.csv'):
        """
        アップロード履歴をCSVに保存

        Args:
            filename (str): 保存先ファイル名
        """
        if not self.upload_history:
            print("保存する履歴がありません")
            return

        try:
            # logsディレクトリに保存
            if not filename.startswith('logs/'):
                filename = os.path.join('logs', filename)

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = self.upload_history[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.upload_history)

            print(f"\nアップロード履歴を保存しました: {filename}")
        except Exception as e:
            print(f"エラー: 履歴の保存に失敗しました: {e}")

    def get_statistics(self):
        """
        アップロード統計を取得

        Returns:
            dict: 統計情報
        """
        if not self.upload_history:
            return None

        total = len(self.upload_history)
        privacy_counts = {}

        for entry in self.upload_history:
            privacy = entry['privacy_status']
            privacy_counts[privacy] = privacy_counts.get(privacy, 0) + 1

        return {
            'total_uploads': total,
            'privacy_status_breakdown': privacy_counts,
            'first_upload': self.upload_history[0]['uploaded_at'],
            'last_upload': self.upload_history[-1]['uploaded_at']
        }

    def upload_from_csv_scheduled(self, csv_file, max_uploads=5, log_file=None):
        """
        CSVファイルから先頭N件をアップロードし、処理済み行を削除
        Windowsタスクスケジューラーでの定期実行に最適

        Args:
            csv_file (str): CSVファイルのパス
            max_uploads (int): 1回の実行で処理する最大件数（デフォルト: 5）
            log_file (str): ログファイルのパス（Noneの場合は自動生成）

        Returns:
            dict: 実行結果のサマリー
        """
        # ログ設定
        if log_file is None:
            log_dir = 'logs'
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f'scheduled_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("スケジュール実行バッチアップロード開始")
        logger.info(f"CSVファイル: {csv_file}")
        logger.info(f"最大アップロード数: {max_uploads}")
        logger.info("=" * 60)

        # CSVファイルの存在確認
        if not os.path.exists(csv_file):
            logger.error(f"CSVファイルが見つかりません: {csv_file}")
            return {'success': False, 'error': 'CSV file not found'}

        # CSVファイルを読み込み
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                all_rows = list(reader)
                fieldnames = reader.fieldnames
        except Exception as e:
            logger.error(f"CSVファイルの読み込みに失敗: {e}")
            return {'success': False, 'error': str(e)}

        if not all_rows:
            logger.info("CSVファイルにデータがありません。すべてのアップロードが完了しています。")
            return {'success': True, 'uploaded': 0, 'remaining': 0, 'message': 'All uploads completed'}

        # 処理する行数を決定
        rows_to_process = all_rows[:max_uploads]
        remaining_rows = all_rows[max_uploads:]

        logger.info(f"CSV内の総行数: {len(all_rows)}")
        logger.info(f"今回処理する行数: {len(rows_to_process)}")
        logger.info(f"処理後の残り行数: {len(remaining_rows)}")
        logger.info("")

        # アップロード結果
        success_count = 0
        failed_count = 0
        results = []

        # 各行を処理
        for i, row in enumerate(rows_to_process, 1):
            logger.info(f"[{i}/{len(rows_to_process)}] 処理中: {row.get('file', 'N/A')}")

            try:
                video_file = row['file']

                # ファイルの存在確認
                if not os.path.exists(video_file):
                    logger.warning(f"動画ファイルが見つかりません: {video_file}")
                    failed_count += 1
                    results.append({
                        'file': video_file,
                        'status': 'failed',
                        'error': 'File not found'
                    })
                    continue

                # タグをリストに変換
                tags = []
                if 'tags' in row and row['tags']:
                    tags = [tag.strip() for tag in row['tags'].split(',')]

                # 再生リスト処理
                playlist_id = None
                if 'playlist_name' in row and row['playlist_name']:
                    playlist_id = self.playlist_manager.get_playlist(row['playlist_name'])
                    if not playlist_id:
                        logger.warning(f"再生リスト '{row['playlist_name']}' が見つかりません。")
                        logger.warning("動画は再生リストなしでアップロードされます。")

                # メタデータ構築
                metadata = {
                    'title': row.get('title', ''),
                    'description': row.get('description', ''),
                    'tags': tags,
                    'category_id': row.get('category_id', '22'),
                    'privacy_status': row.get('privacy_status', 'public'),
                    'playlist_id': playlist_id,
                    'publish_at': row.get('publish_at', None)
                }

                # アップロード実行
                result = upload_with_retry(self.youtube, video_file, metadata)

                if result:
                    logger.info(f"✓ アップロード成功: {result['id']}")
                    logger.info(f"  URL: {result['url']}")
                    success_count += 1
                    results.append({
                        'file': video_file,
                        'status': 'success',
                        'video_id': result['id'],
                        'url': result['url']
                    })
                else:
                    logger.error(f"✗ アップロード失敗: {video_file}")
                    failed_count += 1
                    results.append({
                        'file': video_file,
                        'status': 'failed',
                        'error': 'Upload failed'
                    })

            except Exception as e:
                logger.error(f"エラーが発生しました: {e}")
                failed_count += 1
                results.append({
                    'file': row.get('file', 'N/A'),
                    'status': 'failed',
                    'error': str(e)
                })

            # API制限を考慮して待機
            if i < len(rows_to_process):
                wait_time = 10
                logger.info(f"{wait_time}秒待機...")
                time.sleep(wait_time)

        # CSVファイルを更新（処理済み行を削除）
        try:
            # バックアップを作成
            backup_file = csv_file + '.backup'
            shutil.copy2(csv_file, backup_file)
            logger.info(f"バックアップを作成しました: {backup_file}")

            # 残りの行でCSVを上書き
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(remaining_rows)

            logger.info(f"CSVファイルを更新しました: 処理済み{len(rows_to_process)}行を削除")

        except Exception as e:
            logger.error(f"CSVファイルの更新に失敗しました: {e}")
            logger.error("バックアップファイルから復元してください")

        # サマリー
        logger.info("")
        logger.info("=" * 60)
        logger.info("実行結果サマリー")
        logger.info("=" * 60)
        logger.info(f"成功: {success_count}")
        logger.info(f"失敗: {failed_count}")
        logger.info(f"残りの動画数: {len(remaining_rows)}")
        logger.info(f"ログファイル: {log_file}")
        logger.info("=" * 60)

        if len(remaining_rows) == 0:
            logger.info("🎉 すべての動画のアップロードが完了しました！")

        return {
            'success': True,
            'uploaded': success_count,
            'failed': failed_count,
            'remaining': len(remaining_rows),
            'log_file': log_file,
            'results': results
        }


if __name__ == '__main__':
    # テスト用コード
    import sys

    # 親ディレクトリをパスに追加
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from src.auth import authenticate_youtube

    print("=== YouTube Shorts バッチアップロードテスト ===\n")

    # 認証
    youtube = authenticate_youtube()

    # バッチアップローダーの初期化
    uploader = ShortsBatchUploader(youtube)

    print("\n使用例:")
    print("1. ディレクトリから一括アップロード:")
    print("   uploader.upload_from_directory('shorts_videos', interval_minutes=30)")
    print("\n2. CSVファイルから一括アップロード:")
    print("   uploader.upload_from_csv('upload_list.csv')")
    print("\n3. アップロード履歴を保存:")
    print("   uploader.save_history('upload_history.csv')")
