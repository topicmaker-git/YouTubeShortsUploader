"""
YouTube Shorts アップロードモジュール
動画のアップロードとエラーハンドリングを行います。
"""

import time
from datetime import datetime, timezone, timedelta
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


def convert_jst_to_utc_iso8601(jst_datetime_str):
    """
    日本時間の日時文字列をUTC ISO 8601形式に変換

    Args:
        jst_datetime_str (str): 日本時間の日時文字列
                               形式: "yyyy-mm-dd hh:mm:ss" または "yyyy-mm-dd hh:mm"

    Returns:
        str: UTC ISO 8601形式の文字列 (例: "2025-11-20T01:00:00Z")
             入力がNoneまたは空文字列の場合はNoneを返す

    Examples:
        >>> convert_jst_to_utc_iso8601("2025-11-20 10:00:00")
        "2025-11-20T01:00:00Z"
    """
    if not jst_datetime_str:
        return None

    jst_datetime_str = jst_datetime_str.strip()
    if not jst_datetime_str:
        return None

    # 日時をパース（秒が省略されている場合も対応）
    try:
        # "yyyy-mm-dd hh:mm:ss" 形式
        if len(jst_datetime_str) == 19:
            dt = datetime.strptime(jst_datetime_str, "%Y-%m-%d %H:%M:%S")
        # "yyyy-mm-dd hh:mm" 形式
        elif len(jst_datetime_str) == 16:
            dt = datetime.strptime(jst_datetime_str, "%Y-%m-%d %H:%M")
        else:
            raise ValueError(f"日時形式が不正です: {jst_datetime_str}")
    except ValueError as e:
        print(f"警告: 日時のパースに失敗しました: {e}")
        print(f"正しい形式: 'yyyy-mm-dd hh:mm:ss' または 'yyyy-mm-dd hh:mm'")
        return None

    # 日本時間（UTC+9）として解釈
    jst = timezone(timedelta(hours=9))
    dt_jst = dt.replace(tzinfo=jst)

    # UTCに変換
    dt_utc = dt_jst.astimezone(timezone.utc)

    # ISO 8601形式に変換
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def upload_shorts_video(
    youtube,
    video_file,
    title,
    description,
    tags=None,
    category_id='22',
    privacy_status='public',
    made_for_kids=False,
    publish_at=None,
    playlist_id=None
):
    """
    YouTube Shortsをアップロードする

    Args:
        youtube: YouTube API クライアント
        video_file (str): アップロードする動画ファイルのパス
        title (str): 動画のタイトル
        description (str): 動画の説明文
        tags (list): タグのリスト
        category_id (str): カテゴリID（デフォルト: 22 = People & Blogs）
        privacy_status (str): 公開設定（'public', 'private', 'unlisted'）
        made_for_kids (bool): 子供向けコンテンツかどうか
        publish_at (str): 公開日時（ISO 8601形式: "2025-11-20T10:00:00Z"）
        playlist_id (str): 追加する再生リストID

    Returns:
        dict: アップロード結果（動画ID、URL等）

    Raises:
        HttpError: API呼び出しが失敗した場合
    """
    # Shortsとして認識させるため、タイトルまたは説明文に#Shortsを追加
    if '#Shorts' not in title and '#shorts' not in title:
        title = f"{title} #Shorts"

    if '#Shorts' not in description and '#shorts' not in description:
        description = f"{description}\n\n#Shorts"

    # リクエストボディの構築
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': made_for_kids
        }
    }

    # 公開日時のスケジュール設定
    if publish_at:
        # 日本時間からUTC ISO 8601形式に変換
        publish_at_utc = convert_jst_to_utc_iso8601(publish_at)
        if publish_at_utc:
            body['status']['publishAt'] = publish_at_utc
            # スケジュール公開する場合は一旦privateにする必要がある
            if privacy_status == 'public':
                body['status']['privacyStatus'] = 'private'
            print(f"スケジュール公開設定: {publish_at} (JST) → {publish_at_utc} (UTC)")
        else:
            print(f"警告: 公開日時の形式が不正です: {publish_at}")
            print(f"スケジュール公開は設定されません")

    # メディアファイルのアップロード設定
    # chunksize=-1 は、ファイル全体を一度にアップロードすることを意味します
    media = MediaFileUpload(
        video_file,
        chunksize=-1,
        resumable=True,
        mimetype='video/mp4'
    )

    print(f"\n動画のアップロードを開始します: {video_file}")
    print(f"タイトル: {title}")
    print(f"公開設定: {privacy_status}")

    # アップロードリクエストの実行
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    error = None
    retry = 0

    # チャンク単位でアップロードを実行
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"アップロード進捗: {progress}%", end='\r')
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                # サーバーエラーの場合は再試行
                error = f"サーバーエラー ({e.resp.status})"
                retry += 1
                if retry > 5:
                    raise
                wait_time = retry * 5
                print(f"\n{error}。{wait_time}秒後に再試行します...")
                time.sleep(wait_time)
            else:
                raise

    print(f"\nアップロード完了!")
    print(f"動画ID: {response['id']}")
    print(f"URL: https://youtube.com/shorts/{response['id']}")
    print(f"管理URL: https://studio.youtube.com/video/{response['id']}/edit")

    # 再生リストに追加
    if playlist_id:
        from .playlist_manager import PlaylistManager
        playlist_manager = PlaylistManager(youtube)
        if playlist_manager.add_video_to_playlist(playlist_id, response['id']):
            print(f"再生リスト (ID: {playlist_id}) に追加しました")

    return {
        'id': response['id'],
        'url': f"https://youtube.com/shorts/{response['id']}",
        'studio_url': f"https://studio.youtube.com/video/{response['id']}/edit",
        'title': title,
        'privacy_status': privacy_status
    }


def upload_with_retry(youtube, video_file, metadata, max_retries=3):
    """
    再試行ロジック付きアップロード

    Args:
        youtube: YouTube API クライアント
        video_file (str): 動画ファイルのパス
        metadata (dict): 動画のメタデータ
        max_retries (int): 最大再試行回数

    Returns:
        dict: アップロード結果、失敗した場合はNone
    """
    for attempt in range(max_retries):
        try:
            return upload_shorts_video(
                youtube,
                video_file,
                metadata['title'],
                metadata['description'],
                metadata.get('tags'),
                metadata.get('category_id', '22'),
                metadata.get('privacy_status', 'public'),
                metadata.get('made_for_kids', False),
                metadata.get('publish_at'),
                metadata.get('playlist_id')
            )

        except HttpError as e:
            error_reason = 'unknown'
            if e.error_details:
                error_reason = e.error_details[0].get('reason', 'unknown')

            print(f"\nHTTPエラーが発生しました (試行 {attempt + 1}/{max_retries})")
            print(f"ステータスコード: {e.resp.status}")
            print(f"理由: {error_reason}")

            # 403 Forbidden エラー
            if e.resp.status == 403:
                if error_reason == 'quotaExceeded':
                    print("エラー: APIクォータを超過しました。")
                    print("YouTube Data API v3は1日あたり10,000ユニットの制限があります。")
                    print("24時間後に再試行してください。")
                    break
                elif error_reason == 'forbidden':
                    print("エラー: 権限がありません。")
                    print("OAuth スコープを確認してください。")
                    break
                elif error_reason == 'uploadLimitExceeded':
                    print("エラー: 1日のアップロード上限に達しました。")
                    break

            # 400 Bad Request エラー
            elif e.resp.status == 400:
                if error_reason == 'invalidVideoMetadata':
                    print("エラー: 動画のメタデータが無効です。")
                    print(f"メタデータ: {metadata}")
                    break
                elif error_reason == 'invalidVideo':
                    print("エラー: 動画ファイルが無効です。")
                    break

            # 500系サーバーエラー
            elif e.resp.status in [500, 502, 503, 504]:
                wait_time = (2 ** attempt) * 5  # 指数バックオフ
                print(f"サーバーエラー。{wait_time}秒後に再試行します...")
                time.sleep(wait_time)
                continue

            print(f"詳細: {e}")
            break

        except Exception as e:
            print(f"\n予期しないエラーが発生しました: {e}")
            print(f"試行 {attempt + 1}/{max_retries}")

            if attempt < max_retries - 1:
                wait_time = 5
                print(f"{wait_time}秒後に再試行します...")
                time.sleep(wait_time)
            else:
                break

    return None


# カテゴリIDの参考情報
YOUTUBE_CATEGORIES = {
    '1': 'Film & Animation',
    '2': 'Autos & Vehicles',
    '10': 'Music',
    '15': 'Pets & Animals',
    '17': 'Sports',
    '19': 'Travel & Events',
    '20': 'Gaming',
    '22': 'People & Blogs',
    '23': 'Comedy',
    '24': 'Entertainment',
    '25': 'News & Politics',
    '26': 'Howto & Style',
    '27': 'Education',
    '28': 'Science & Technology',
    '29': 'Nonprofits & Activism'
}


if __name__ == '__main__':
    # テスト用コード
    import sys
    import os

    # 親ディレクトリをパスに追加
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from src.auth import authenticate_youtube

    print("=== YouTube Shorts アップロードテスト ===\n")

    # 認証
    youtube = authenticate_youtube()

    # テスト用のメタデータ
    test_metadata = {
        'title': 'テスト動画',
        'description': 'YouTube Shorts Uploaderのテストです',
        'tags': ['テスト', 'Shorts', 'Python'],
        'category_id': '28',  # Science & Technology
        'privacy_status': 'private'  # テストなのでprivate
    }

    print("\n利用可能なカテゴリ:")
    for cat_id, cat_name in YOUTUBE_CATEGORIES.items():
        print(f"  {cat_id}: {cat_name}")

    print("\n動画ファイルのパスを指定してアップロードをテストできます")
    print("（このテストコードは実際にアップロードを実行します）")
