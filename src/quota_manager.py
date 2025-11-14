"""
YouTube API クォータ管理モジュール
API使用量を追跡し、1日の上限を管理します。
"""

import os
import json
from datetime import datetime, timedelta


class QuotaManager:
    """YouTube API クォータ管理クラス"""

    # YouTube Data API v3のコスト
    API_COSTS = {
        'video.insert': 1600,  # 動画アップロード
        'video.list': 1,       # 動画情報取得
        'video.update': 50,    # 動画情報更新
        'channel.list': 1,     # チャンネル情報取得
    }

    def __init__(self, daily_limit=10000, state_file='quota_state.json'):
        """
        初期化

        Args:
            daily_limit (int): 1日あたりのクォータ上限（デフォルト: 10000）
            state_file (str): 状態保存ファイルのパス
        """
        self.daily_limit = daily_limit
        self.state_file = state_file
        self.current_usage = 0
        self.reset_time = None

        # 状態をロード
        self.load_quota_state()

    def load_quota_state(self):
        """
        保存された状態をロード
        """
        if not os.path.exists(self.state_file):
            self.reset_quota()
            return

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            self.current_usage = state.get('current_usage', 0)
            reset_time_str = state.get('reset_time')

            if reset_time_str:
                self.reset_time = datetime.fromisoformat(reset_time_str)

                # リセット時刻を過ぎている場合はリセット
                if datetime.now() >= self.reset_time:
                    self.reset_quota()
            else:
                self.reset_quota()

        except (json.JSONDecodeError, ValueError) as e:
            print(f"警告: 状態ファイルの読み込みに失敗しました: {e}")
            self.reset_quota()

    def reset_quota(self):
        """
        クォータをリセット
        """
        self.current_usage = 0
        # 次のリセット時刻を設定（太平洋時間の午前0時 = 日本時間の午後5時）
        now = datetime.now()
        self.reset_time = now.replace(hour=17, minute=0, second=0, microsecond=0)

        # もし現在時刻がリセット時刻を過ぎている場合は、翌日に設定
        if now >= self.reset_time:
            self.reset_time += timedelta(days=1)

        self.save_quota_state()

    def save_quota_state(self):
        """
        現在の状態を保存
        """
        state = {
            'current_usage': self.current_usage,
            'reset_time': self.reset_time.isoformat() if self.reset_time else None,
            'daily_limit': self.daily_limit,
            'last_updated': datetime.now().isoformat()
        }

        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, indent=2, fp=f)
        except Exception as e:
            print(f"警告: 状態の保存に失敗しました: {e}")

    def can_upload(self, cost=None):
        """
        アップロードが可能かチェック

        Args:
            cost (int): 操作のコスト（デフォルト: video.insertのコスト）

        Returns:
            bool: アップロード可能な場合True
        """
        if cost is None:
            cost = self.API_COSTS['video.insert']

        return (self.current_usage + cost) <= self.daily_limit

    def use_quota(self, operation='video.insert', cost=None):
        """
        クォータを使用

        Args:
            operation (str): 操作名
            cost (int): コスト（指定しない場合は操作名から自動取得）

        Returns:
            bool: 成功した場合True
        """
        if cost is None:
            cost = self.API_COSTS.get(operation, 0)

        if not self.can_upload(cost):
            return False

        self.current_usage += cost
        self.save_quota_state()
        return True

    def get_remaining_quota(self):
        """
        残りのクォータを取得

        Returns:
            int: 残りのクォータ
        """
        return max(0, self.daily_limit - self.current_usage)

    def get_remaining_uploads(self):
        """
        残りのアップロード可能回数を取得

        Returns:
            int: 残りのアップロード回数
        """
        upload_cost = self.API_COSTS['video.insert']
        return self.get_remaining_quota() // upload_cost

    def get_reset_time_remaining(self):
        """
        リセットまでの残り時間を取得

        Returns:
            timedelta: リセットまでの時間
        """
        if not self.reset_time:
            return timedelta(0)

        remaining = self.reset_time - datetime.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def print_status(self):
        """
        現在のクォータ状態を表示
        """
        print("\n=== YouTube API クォータ状態 ===")
        print(f"使用量: {self.current_usage} / {self.daily_limit} ユニット")
        print(f"残りクォータ: {self.get_remaining_quota()} ユニット")
        print(f"残りアップロード回数: {self.get_remaining_uploads()} 回")

        if self.reset_time:
            remaining = self.get_reset_time_remaining()
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            print(f"リセットまで: {hours}時間{minutes}分")
            print(f"リセット時刻: {self.reset_time.strftime('%Y-%m-%d %H:%M:%S')}")

        usage_percent = (self.current_usage / self.daily_limit) * 100
        print(f"使用率: {usage_percent:.1f}%")

        # プログレスバーを表示
        bar_length = 40
        filled_length = int(bar_length * self.current_usage / self.daily_limit)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f"[{bar}]")


class QuotaExceededError(Exception):
    """クォータ超過エラー"""
    pass


def check_quota_before_upload(quota_manager, count=1):
    """
    アップロード前にクォータをチェックするデコレータ

    Args:
        quota_manager (QuotaManager): クォータマネージャー
        count (int): アップロード数

    Raises:
        QuotaExceededError: クォータが不足している場合
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            upload_cost = QuotaManager.API_COSTS['video.insert'] * count

            if not quota_manager.can_upload(upload_cost):
                remaining = quota_manager.get_remaining_uploads()
                reset_time = quota_manager.get_reset_time_remaining()

                hours = int(reset_time.total_seconds() // 3600)
                minutes = int((reset_time.total_seconds() % 3600) // 60)

                raise QuotaExceededError(
                    f"クォータが不足しています。\n"
                    f"必要: {count}回のアップロード\n"
                    f"残り: {remaining}回のアップロード\n"
                    f"リセットまで: {hours}時間{minutes}分"
                )

            # 実行前にクォータを確保
            quota_manager.use_quota('video.insert', upload_cost)

            # 関数を実行
            result = func(*args, **kwargs)

            return result

        return wrapper
    return decorator


if __name__ == '__main__':
    # テスト用コード
    print("=== YouTube API クォータ管理テスト ===\n")

    # クォータマネージャーの初期化
    quota_manager = QuotaManager()

    # 現在の状態を表示
    quota_manager.print_status()

    # アップロード可能かチェック
    print("\n=== アップロード可能性チェック ===")
    if quota_manager.can_upload():
        print("✓ アップロード可能です")
    else:
        print("✗ クォータが不足しています")

    # シミュレーション
    print("\n=== シミュレーション ===")
    print("1回のアップロードをシミュレート...")

    if quota_manager.use_quota('video.insert'):
        print("✓ アップロード成功（シミュレーション）")
        quota_manager.print_status()
    else:
        print("✗ クォータ不足")

    # API コスト一覧
    print("\n=== API コスト一覧 ===")
    for operation, cost in QuotaManager.API_COSTS.items():
        print(f"  {operation}: {cost} ユニット")
