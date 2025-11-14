"""
YouTube API認証モジュール
OAuth 2.0認証を使用してYouTube Data API v3にアクセスします。
"""

import os
import glob
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# 認証スコープの定義
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]


def find_client_secret_file():
    """
    client_secret.jsonファイルを探す

    Returns:
        str: client_secretファイルのパス

    Raises:
        FileNotFoundError: client_secretファイルが見つからない場合
    """
    # カレントディレクトリで検索
    patterns = [
        'client_secret.json',
        'client_secret*.json',
        '../client_secret*.json'
    ]

    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]

    raise FileNotFoundError(
        "client_secret.jsonファイルが見つかりません。\n"
        "Google Cloud Consoleからダウンロードした認証情報ファイルを\n"
        "プロジェクトのルートディレクトリに配置してください。"
    )


def authenticate_youtube(token_file='token.json', client_secret_file=None):
    """
    YouTube APIの認証を行う

    Args:
        token_file (str): 認証トークンを保存するファイルのパス
        client_secret_file (str): クライアントシークレットファイルのパス

    Returns:
        googleapiclient.discovery.Resource: YouTube API クライアント
    """
    creds = None

    # トークンファイルが存在する場合は読み込む
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            print(f"既存の認証情報を読み込みました: {token_file}")
        except Exception as e:
            print(f"トークンファイルの読み込みに失敗しました: {e}")
            creds = None

    # 有効な認証情報がない場合は新規取得
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("認証トークンを更新しています...")
                creds.refresh(Request())
                print("認証トークンの更新が完了しました")
            except Exception as e:
                print(f"トークンの更新に失敗しました: {e}")
                creds = None

        if not creds:
            # client_secretファイルを探す
            if not client_secret_file:
                client_secret_file = find_client_secret_file()

            print(f"OAuth 2.0認証を開始します...")
            print(f"使用する認証情報ファイル: {client_secret_file}")
            print("ブラウザが開きますので、Googleアカウントでログインしてください。")

            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
            print("認証が完了しました")

        # トークンを保存
        try:
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"認証トークンを保存しました: {token_file}")
        except Exception as e:
            print(f"警告: トークンの保存に失敗しました: {e}")

    # YouTube APIクライアントを構築
    youtube = build('youtube', 'v3', credentials=creds)
    print("YouTube APIクライアントの初期化が完了しました")

    return youtube


def get_channel_info(youtube):
    """
    認証されたチャンネルの情報を取得する

    Args:
        youtube: YouTube API クライアント

    Returns:
        dict: チャンネル情報
    """
    try:
        request = youtube.channels().list(
            part='snippet,statistics',
            mine=True
        )
        response = request.execute()

        if response['items']:
            channel = response['items'][0]
            return {
                'id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'subscriber_count': channel['statistics'].get('subscriberCount', '非公開'),
                'video_count': channel['statistics'].get('videoCount', '0'),
                'view_count': channel['statistics'].get('viewCount', '0')
            }
        else:
            return None
    except Exception as e:
        print(f"チャンネル情報の取得に失敗しました: {e}")
        return None


if __name__ == '__main__':
    # テスト用コード
    print("=== YouTube API 認証テスト ===\n")

    try:
        youtube = authenticate_youtube()
        print("\n=== 認証成功 ===\n")

        print("チャンネル情報を取得しています...")
        channel_info = get_channel_info(youtube)

        if channel_info:
            print("\n=== チャンネル情報 ===")
            print(f"チャンネル名: {channel_info['title']}")
            print(f"チャンネルID: {channel_info['id']}")
            print(f"登録者数: {channel_info['subscriber_count']}")
            print(f"動画数: {channel_info['video_count']}")
            print(f"総再生回数: {channel_info['view_count']}")
        else:
            print("チャンネル情報が取得できませんでした")

    except Exception as e:
        print(f"\n=== 認証エラー ===")
        print(f"エラー: {e}")
