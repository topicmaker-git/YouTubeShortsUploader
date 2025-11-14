"""
YouTube Shorts Uploader

YouTube Data API v3を使用してShorts動画を自動アップロードするツール
"""

__version__ = '1.0.0'
__author__ = 'YouTube Shorts Uploader'

from .auth import authenticate_youtube, get_channel_info
from .uploader import upload_shorts_video, upload_with_retry
from .batch_uploader import ShortsBatchUploader
from .validator import ShortsValidator
from .quota_manager import QuotaManager, QuotaExceededError

__all__ = [
    'authenticate_youtube',
    'get_channel_info',
    'upload_shorts_video',
    'upload_with_retry',
    'ShortsBatchUploader',
    'ShortsValidator',
    'QuotaManager',
    'QuotaExceededError',
]
