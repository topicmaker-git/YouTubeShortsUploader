#!/usr/bin/env python3
"""
YouTube Shorts Uploader - メインスクリプト

YouTube Shorts動画を自動アップロードするコマンドラインツール
"""

import sys
import argparse
from src import (
    authenticate_youtube,
    get_channel_info,
    upload_shorts_video,
    ShortsBatchUploader,
    ShortsValidator,
    QuotaManager
)


def cmd_auth(args):
    """認証コマンド"""
    print("=== YouTube API 認証 ===\n")

    youtube = authenticate_youtube()
    print("\n認証が完了しました！")

    # チャンネル情報を表示
    if args.show_info:
        print("\nチャンネル情報を取得しています...")
        channel_info = get_channel_info(youtube)

        if channel_info:
            print("\n=== チャンネル情報 ===")
            print(f"チャンネル名: {channel_info['title']}")
            print(f"チャンネルID: {channel_info['id']}")
            print(f"登録者数: {channel_info['subscriber_count']}")
            print(f"動画数: {channel_info['video_count']}")
            print(f"総再生回数: {channel_info['view_count']}")


def cmd_upload(args):
    """単一動画アップロードコマンド"""
    print("=== YouTube Shorts アップロード ===\n")

    # 認証
    youtube = authenticate_youtube()

    # クォータチェック
    if not args.skip_quota_check:
        quota_manager = QuotaManager()
        quota_manager.print_status()

        if not quota_manager.can_upload():
            print("\nエラー: APIクォータが不足しています")
            return

    # 動画検証
    if not args.skip_validation:
        print("\n動画を検証しています...")
        result, specs = ShortsValidator.check_video_specs(args.video_file)
        ShortsValidator.print_validation_result(args.video_file, result, specs)

        if not result:
            if not args.force:
                print("\nエラー: 動画がShorts要件を満たしていません")
                print("強制的にアップロードする場合は --force オプションを使用してください")
                return
            else:
                print("\n警告: 要件を満たしていませんが、強制的にアップロードします")

    # 再生リスト処理
    playlist_id = None
    if args.playlist:
        from src.playlist_manager import PlaylistManager
        playlist_manager = PlaylistManager(youtube)
        playlist_id = playlist_manager.get_playlist(args.playlist)
        if not playlist_id:
            print(f"\n警告: 再生リスト '{args.playlist}' が見つかりません。")
            print(f"動画は再生リストなしでアップロードされます。")
            print(f"YouTube Studioで後から追加してください。\n")

    # メタデータの設定
    metadata = {
        'title': args.title,
        'description': args.description or '',
        'tags': args.tags.split(',') if args.tags else [],
        'category_id': args.category,
        'privacy_status': args.privacy,
        'playlist_id': playlist_id,
        'publish_at': args.publish_at
    }

    print("\n=== アップロード情報 ===")
    print(f"ファイル: {args.video_file}")
    print(f"タイトル: {metadata['title']}")
    print(f"公開設定: {metadata['privacy_status']}")
    if args.playlist:
        print(f"再生リスト: {args.playlist}")
    if args.publish_at:
        print(f"公開予定日時: {args.publish_at}")

    # アップロード実行
    print("\nアップロードを開始します...")
    from src.uploader import upload_with_retry
    result = upload_with_retry(youtube, args.video_file, metadata)

    if result:
        print("\n=== アップロード成功 ===")
        print(f"動画ID: {result['id']}")
        print(f"URL: {result['url']}")
        print(f"管理URL: {result['studio_url']}")

        # クォータを更新
        if not args.skip_quota_check:
            quota_manager.use_quota('video.insert')
    else:
        print("\nアップロードに失敗しました")


def cmd_batch_upload(args):
    """バッチアップロードコマンド"""
    print("=== YouTube Shorts バッチアップロード ===\n")

    # 認証
    youtube = authenticate_youtube()

    # クォータチェック
    quota_manager = QuotaManager()
    quota_manager.print_status()

    # バッチアップローダーの初期化
    uploader = ShortsBatchUploader(youtube)

    # アップロード実行
    if args.csv_file:
        # CSVから
        results = uploader.upload_from_csv(args.csv_file)
    else:
        # ディレクトリから
        results = uploader.upload_from_directory(
            args.directory,
            pattern=args.pattern,
            interval_minutes=args.interval
        )

    # 履歴を保存
    if results and args.save_history:
        uploader.save_history()

    # 統計を表示
    stats = uploader.get_statistics()
    if stats:
        print("\n=== アップロード統計 ===")
        print(f"合計アップロード数: {stats['total_uploads']}")
        print(f"公開設定内訳: {stats['privacy_status_breakdown']}")


def cmd_validate(args):
    """動画検証コマンド"""
    print("=== YouTube Shorts 動画検証 ===\n")

    if args.directory:
        # ディレクトリ検証
        ShortsValidator.validate_directory(args.directory, args.pattern)
    else:
        # 単一ファイル検証
        result, specs = ShortsValidator.check_video_specs(args.video_file)
        ShortsValidator.print_validation_result(args.video_file, result, specs)


def cmd_quota(args):
    """クォータ管理コマンド"""
    print("=== YouTube API クォータ管理 ===\n")

    quota_manager = QuotaManager()

    if args.reset:
        print("クォータをリセットします...")
        quota_manager.reset_quota()
        print("リセット完了")

    quota_manager.print_status()


def cmd_scheduled_upload(args):
    """スケジュール実行用バッチアップロードコマンド"""
    import sys

    # 認証
    youtube = authenticate_youtube()

    # バッチアップローダーの初期化
    uploader = ShortsBatchUploader(youtube)

    # スケジュール実行
    result = uploader.upload_from_csv_scheduled(
        args.csv_file,
        max_uploads=args.max_uploads,
        log_file=args.log_file
    )

    # 終了コードを設定（失敗時は1を返す）
    if not result['success'] or result['failed'] > 0:
        sys.exit(1)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='YouTube Shorts Uploader - YouTube Shorts動画を自動アップロード',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='コマンド')

    # 認証コマンド
    auth_parser = subparsers.add_parser('auth', help='YouTube APIの認証')
    auth_parser.add_argument('--show-info', action='store_true', help='チャンネル情報を表示')
    auth_parser.set_defaults(func=cmd_auth)

    # アップロードコマンド
    upload_parser = subparsers.add_parser('upload', help='単一動画をアップロード')
    upload_parser.add_argument('video_file', help='動画ファイルのパス')
    upload_parser.add_argument('-t', '--title', required=True, help='動画のタイトル')
    upload_parser.add_argument('-d', '--description', help='動画の説明文')
    upload_parser.add_argument('--tags', help='タグ（カンマ区切り）')
    upload_parser.add_argument('-c', '--category', default='22', help='カテゴリID（デフォルト: 22）')
    upload_parser.add_argument('-p', '--privacy', choices=['public', 'private', 'unlisted'],
                              default='public', help='公開設定')
    upload_parser.add_argument('--playlist', help='追加する再生リスト名')
    upload_parser.add_argument('--publish-at', dest='publish_at',
                              help='公開予定日時（ISO 8601形式: 2025-11-20T10:00:00Z）')
    upload_parser.add_argument('--skip-validation', action='store_true', help='動画検証をスキップ')
    upload_parser.add_argument('--skip-quota-check', action='store_true', help='クォータチェックをスキップ')
    upload_parser.add_argument('--force', action='store_true', help='検証エラーを無視して強制アップロード')
    upload_parser.set_defaults(func=cmd_upload)

    # バッチアップロードコマンド
    batch_parser = subparsers.add_parser('batch', help='複数動画を一括アップロード')
    batch_parser.add_argument('-d', '--directory', help='動画ディレクトリ')
    batch_parser.add_argument('-c', '--csv-file', help='メタデータCSVファイル')
    batch_parser.add_argument('--pattern', default='*.mp4', help='ファイルパターン（デフォルト: *.mp4）')
    batch_parser.add_argument('-i', '--interval', type=int, default=30,
                            help='アップロード間隔（分、デフォルト: 30）')
    batch_parser.add_argument('--save-history', action='store_true', help='アップロード履歴を保存')
    batch_parser.set_defaults(func=cmd_batch_upload)

    # 検証コマンド
    validate_parser = subparsers.add_parser('validate', help='動画がShorts要件を満たすか検証')
    validate_parser.add_argument('video_file', nargs='?', help='動画ファイルのパス')
    validate_parser.add_argument('-d', '--directory', help='ディレクトリを検証')
    validate_parser.add_argument('--pattern', default='*.mp4', help='ファイルパターン（デフォルト: *.mp4）')
    validate_parser.set_defaults(func=cmd_validate)

    # クォータ管理コマンド
    quota_parser = subparsers.add_parser('quota', help='APIクォータの状態を確認')
    quota_parser.add_argument('--reset', action='store_true', help='クォータをリセット')
    quota_parser.set_defaults(func=cmd_quota)

    # スケジュール実行コマンド
    scheduled_parser = subparsers.add_parser('scheduled',
                                            help='スケジュール実行用バッチアップロード（タスクスケジューラー用）')
    scheduled_parser.add_argument('-c', '--csv-file', default='upload_list.csv',
                                 help='メタデータCSVファイル（デフォルト: upload_list.csv）')
    scheduled_parser.add_argument('-n', '--max-uploads', type=int, default=5,
                                 help='1回の実行で処理する最大件数（デフォルト: 5）')
    scheduled_parser.add_argument('--log-file', help='ログファイルのパス（指定しない場合は自動生成）')
    scheduled_parser.set_defaults(func=cmd_scheduled_upload)

    # 引数をパース
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # コマンドを実行
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n操作が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
