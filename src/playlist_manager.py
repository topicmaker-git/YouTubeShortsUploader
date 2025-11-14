"""
YouTube 再生リスト管理モジュール
再生リストの作成、検索、動画の追加を行います。
"""

from googleapiclient.errors import HttpError


class PlaylistManager:
    """YouTube 再生リスト管理クラス"""

    def __init__(self, youtube_client):
        """
        初期化

        Args:
            youtube_client: YouTube API クライアント
        """
        self.youtube = youtube_client
        self.playlist_cache = {}  # プレイリスト名 -> プレイリストID のキャッシュ

    def get_playlist(self, playlist_name):
        """
        再生リストを取得（見つからない場合はNoneを返す）

        Args:
            playlist_name (str): 再生リスト名

        Returns:
            str: 再生リストID、見つからない場合はNone
        """
        # キャッシュをチェック
        if playlist_name in self.playlist_cache:
            return self.playlist_cache[playlist_name]

        # 既存の再生リストを検索
        playlist_id = self.find_playlist_by_name(playlist_name)

        if playlist_id:
            # 見つかった場合はキャッシュに保存
            self.playlist_cache[playlist_name] = playlist_id
            return playlist_id

        # 見つからない場合はNoneを返す
        return None

    def get_or_create_playlist(self, playlist_name, description=None, privacy_status='public'):
        """
        再生リストを取得または作成（主にテスト・スクリプト用）

        Args:
            playlist_name (str): 再生リスト名
            description (str): 再生リストの説明（新規作成時）
            privacy_status (str): 公開設定（'public', 'private', 'unlisted'）

        Returns:
            str: 再生リストID、失敗した場合はNone
        """
        # 既存の再生リストを検索
        playlist_id = self.get_playlist(playlist_name)

        if playlist_id:
            return playlist_id

        # 見つからない場合は新規作成
        print(f"再生リスト '{playlist_name}' が見つかりません。新規作成します...")
        playlist_id = self.create_playlist(
            playlist_name,
            description or f"YouTube Shorts: {playlist_name}",
            privacy_status
        )

        if playlist_id:
            self.playlist_cache[playlist_name] = playlist_id

        return playlist_id

    def find_playlist_by_name(self, playlist_name):
        """
        再生リストを名前で検索

        Args:
            playlist_name (str): 再生リスト名

        Returns:
            str: 再生リストID、見つからない場合はNone
        """
        try:
            # 自分の再生リストを取得
            request = self.youtube.playlists().list(
                part='snippet',
                mine=True,
                maxResults=50
            )

            while request:
                response = request.execute()

                for item in response.get('items', []):
                    if item['snippet']['title'] == playlist_name:
                        playlist_id = item['id']
                        print(f"既存の再生リスト '{playlist_name}' を見つけました (ID: {playlist_id})")
                        return playlist_id

                # 次のページがあれば取得
                request = self.youtube.playlists().list_next(request, response)

            return None

        except HttpError as e:
            print(f"再生リストの検索に失敗しました: {e}")
            return None

    def create_playlist(self, title, description, privacy_status='public'):
        """
        新しい再生リストを作成

        Args:
            title (str): 再生リストのタイトル
            description (str): 再生リストの説明
            privacy_status (str): 公開設定

        Returns:
            str: 作成した再生リストID、失敗した場合はNone
        """
        try:
            request = self.youtube.playlists().insert(
                part='snippet,status',
                body={
                    'snippet': {
                        'title': title,
                        'description': description
                    },
                    'status': {
                        'privacyStatus': privacy_status
                    }
                }
            )

            response = request.execute()
            playlist_id = response['id']

            print(f"再生リスト '{title}' を作成しました (ID: {playlist_id})")
            return playlist_id

        except HttpError as e:
            print(f"再生リストの作成に失敗しました: {e}")
            return None

    def add_video_to_playlist(self, playlist_id, video_id, position=None):
        """
        動画を再生リストに追加

        Args:
            playlist_id (str): 再生リストID
            video_id (str): 動画ID
            position (int): 再生リスト内の位置（Noneの場合は末尾）

        Returns:
            bool: 成功した場合True
        """
        try:
            body = {
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }

            if position is not None:
                body['snippet']['position'] = position

            request = self.youtube.playlistItems().insert(
                part='snippet',
                body=body
            )

            request.execute()
            print(f"動画 {video_id} を再生リストに追加しました")
            return True

        except HttpError as e:
            print(f"動画を再生リストに追加できませんでした: {e}")
            return False

    def list_playlists(self):
        """
        自分の再生リスト一覧を取得

        Returns:
            list: 再生リスト情報のリスト
        """
        playlists = []

        try:
            request = self.youtube.playlists().list(
                part='snippet,contentDetails',
                mine=True,
                maxResults=50
            )

            while request:
                response = request.execute()

                for item in response.get('items', []):
                    playlists.append({
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'item_count': item['contentDetails']['itemCount'],
                        'privacy_status': item.get('status', {}).get('privacyStatus', 'unknown')
                    })

                request = self.youtube.playlists().list_next(request, response)

            return playlists

        except HttpError as e:
            print(f"再生リスト一覧の取得に失敗しました: {e}")
            return []


if __name__ == '__main__':
    # テスト用コード
    import sys
    import os

    # 親ディレクトリをパスに追加
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from src.auth import authenticate_youtube

    print("=== YouTube 再生リスト管理テスト ===\n")

    # 認証
    youtube = authenticate_youtube()

    # 再生リストマネージャーの初期化
    manager = PlaylistManager(youtube)

    # 再生リスト一覧を取得
    print("\n=== 既存の再生リスト ===")
    playlists = manager.list_playlists()

    if playlists:
        for pl in playlists:
            print(f"- {pl['title']} (動画数: {pl['item_count']}, ID: {pl['id']})")
    else:
        print("再生リストがありません")
