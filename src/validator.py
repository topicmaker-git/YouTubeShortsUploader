"""
YouTube Shorts 動画検証モジュール
動画ファイルがShorts要件を満たしているか検証します。
"""

import os
import subprocess
import json


class ShortsValidator:
    """YouTube Shorts 動画検証クラス"""

    # YouTube Shortsの仕様
    SHORTS_SPECS = {
        'max_duration': 180,  # 最大180秒（3分）
        'recommended_duration': 60,  # 推奨60秒
        'aspect_ratios': {
            '9:16': (9, 16),  # 縦型（推奨）
            '1:1': (1, 1)     # 正方形
        },
        'min_resolution': 720,  # 最小解像度（720p以上）
        'recommended_resolution': 1080,  # 推奨解像度（1080p）
        'max_file_size': 128 * 1024 * 1024 * 1024  # 最大128GB（API経由）
    }

    @staticmethod
    def find_ffprobe():
        """
        ffprobeのパスを検索

        Returns:
            str or None: ffprobeのパス、見つからない場合はNone
        """
        # 1. システムのPATHから検索
        try:
            subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True,
                check=True
            )
            return 'ffprobe'
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # 2. プロジェクト内のポータブル版を検索（Windows）
        portable_paths = [
            os.path.join('ffmpeg', 'bin', 'ffprobe.exe'),
            os.path.join('..', 'ffmpeg', 'bin', 'ffprobe.exe'),
        ]

        for path in portable_paths:
            if os.path.exists(path):
                try:
                    subprocess.run(
                        [path, '-version'],
                        capture_output=True,
                        check=True
                    )
                    return path
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass

        return None

    @staticmethod
    def check_ffprobe_installed():
        """
        ffprobeがインストールされているか確認

        Returns:
            bool: インストールされている場合True
        """
        return ShortsValidator.find_ffprobe() is not None

    @staticmethod
    def get_video_info(video_file):
        """
        動画ファイルの情報を取得

        Args:
            video_file (str): 動画ファイルのパス

        Returns:
            dict: 動画情報、取得に失敗した場合はNone
        """
        if not os.path.exists(video_file):
            print(f"エラー: ファイルが見つかりません: {video_file}")
            return None

        ffprobe_path = ShortsValidator.find_ffprobe()
        if not ffprobe_path:
            print("警告: ffprobeがインストールされていません")
            print("動画の詳細情報を取得するには、ffmpegをインストールしてください")
            print("Windows: run install_ffmpeg_portable.bat")
            print("Ubuntu/Debian: sudo apt-get install ffmpeg")
            print("macOS: brew install ffmpeg")
            return None

        try:
            cmd = [
                ffprobe_path,
                '-v', 'error',
                '-print_format', 'json',
                '-show_streams',
                '-show_format',
                video_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_info = json.loads(result.stdout)

            return video_info

        except subprocess.CalledProcessError as e:
            print(f"エラー: ffprobeの実行に失敗しました: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"エラー: ffprobeの出力を解析できませんでした: {e}")
            return None

    @staticmethod
    def check_video_specs(video_file):
        """
        動画ファイルがShorts要件を満たしているか検証

        Args:
            video_file (str): 動画ファイルのパス

        Returns:
            tuple: (bool, dict or str) - (検証結果, 動画情報またはエラーメッセージ)
        """
        video_info = ShortsValidator.get_video_info(video_file)

        if not video_info:
            return False, "動画情報を取得できませんでした"

        # ビデオストリームを取得
        video_stream = next(
            (s for s in video_info.get('streams', []) if s.get('codec_type') == 'video'),
            None
        )

        if not video_stream:
            return False, "ビデオストリームが見つかりません"

        # 基本情報の取得
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        duration = float(video_info.get('format', {}).get('duration', 0))
        file_size = int(video_info.get('format', {}).get('size', 0))

        # アスペクト比の計算
        if height == 0:
            return False, "動画の高さが0です"

        aspect_ratio = width / height

        # 動画情報をまとめる
        specs = {
            'width': width,
            'height': height,
            'duration': duration,
            'file_size': file_size,
            'aspect_ratio': f"{width}:{height}",
            'aspect_ratio_decimal': round(aspect_ratio, 3),
            'is_vertical': aspect_ratio < 1,
            'is_square': abs(aspect_ratio - 1.0) < 0.1,
            'codec': video_stream.get('codec_name', 'unknown'),
            'fps': eval(video_stream.get('r_frame_rate', '0/1'))
        }

        # Shorts要件の検証
        # 解像度は警告のみとし、エラーにしない
        checks = {
            'duration': duration <= ShortsValidator.SHORTS_SPECS['max_duration'],
            'aspect_ratio': specs['is_vertical'] or specs['is_square'],
            'file_size': file_size <= ShortsValidator.SHORTS_SPECS['max_file_size']
        }

        # 解像度チェック（警告のみ、エラーにしない）
        resolution_ok = (height >= ShortsValidator.SHORTS_SPECS['min_resolution'] or
                        width >= ShortsValidator.SHORTS_SPECS['min_resolution'])

        specs['checks'] = checks
        specs['resolution_ok'] = resolution_ok
        specs['is_valid'] = all(checks.values())

        # 警告とエラーメッセージの生成
        messages = []

        if not checks['duration']:
            messages.append(f"✗ 動画の長さが{ShortsValidator.SHORTS_SPECS['max_duration']}秒を超えています（{duration:.1f}秒）")
        elif duration > ShortsValidator.SHORTS_SPECS['recommended_duration']:
            messages.append(f"⚠ 動画の長さが推奨される{ShortsValidator.SHORTS_SPECS['recommended_duration']}秒を超えています（{duration:.1f}秒）")

        # 解像度は警告のみ（エラーにしない）
        if not resolution_ok:
            messages.append(f"⚠ 解像度が低いです（{width}x{height}）")
            messages.append(f"  推奨: {ShortsValidator.SHORTS_SPECS['min_resolution']}p以上")
        elif (height < ShortsValidator.SHORTS_SPECS['recommended_resolution'] and
              width < ShortsValidator.SHORTS_SPECS['recommended_resolution']):
            messages.append(f"⚠ 解像度が推奨値より低いです（{width}x{height}）")
            messages.append(f"  推奨: {ShortsValidator.SHORTS_SPECS['recommended_resolution']}p以上")

        if not checks['aspect_ratio']:
            messages.append(f"✗ アスペクト比が要件を満たしていません（{specs['aspect_ratio_decimal']}）")
            messages.append("  推奨: 9:16（縦型）または 1:1（正方形）")

        if not checks['file_size']:
            messages.append(f"✗ ファイルサイズが大きすぎます（{file_size / (1024**3):.2f} GB）")

        specs['messages'] = messages

        return specs['is_valid'], specs

    @staticmethod
    def print_validation_result(video_file, result, specs):
        """
        検証結果を表示

        Args:
            video_file (str): 動画ファイルのパス
            result (bool): 検証結果
            specs (dict or str): 動画情報またはエラーメッセージ
        """
        print(f"\n=== 動画検証結果: {os.path.basename(video_file)} ===")

        if isinstance(specs, str):
            # エラーメッセージの場合
            print(f"エラー: {specs}")
            return

        # 基本情報
        print(f"\n【基本情報】")
        print(f"  解像度: {specs['width']}x{specs['height']}")
        print(f"  アスペクト比: {specs['aspect_ratio']} ({specs['aspect_ratio_decimal']})")
        print(f"  動画の長さ: {specs['duration']:.1f}秒")
        print(f"  ファイルサイズ: {specs['file_size'] / (1024**2):.2f} MB")
        print(f"  コーデック: {specs['codec']}")
        print(f"  フレームレート: {specs['fps']:.2f} fps")

        # 検証結果
        print(f"\n【検証結果】")
        if result:
            print("✓ この動画はYouTube Shortsの要件を満たしています")
        else:
            print("✗ この動画はYouTube Shortsの要件を満たしていません")

        # 詳細メッセージ
        if specs.get('messages'):
            print(f"\n【詳細】")
            for message in specs['messages']:
                print(f"  {message}")

    @staticmethod
    def validate_directory(directory, pattern='*.mp4'):
        """
        ディレクトリ内の全動画ファイルを検証

        Args:
            directory (str): ディレクトリのパス
            pattern (str): ファイルパターン

        Returns:
            dict: 検証結果のサマリー
        """
        import glob

        search_pattern = os.path.join(directory, pattern)
        video_files = sorted(glob.glob(search_pattern))

        if not video_files:
            print(f"警告: {search_pattern} に一致するファイルが見つかりませんでした")
            return {'total': 0, 'valid': 0, 'invalid': 0}

        print(f"\n=== ディレクトリ検証: {directory} ===")
        print(f"{len(video_files)}個の動画ファイルが見つかりました\n")

        valid_count = 0
        invalid_count = 0
        results = []

        for video_file in video_files:
            result, specs = ShortsValidator.check_video_specs(video_file)

            if result:
                valid_count += 1
                status = "✓"
            else:
                invalid_count += 1
                status = "✗"

            print(f"{status} {os.path.basename(video_file)}")

            results.append({
                'file': video_file,
                'valid': result,
                'specs': specs
            })

        print(f"\n=== 検証サマリー ===")
        print(f"合計: {len(video_files)}")
        print(f"有効: {valid_count}")
        print(f"無効: {invalid_count}")

        return {
            'total': len(video_files),
            'valid': valid_count,
            'invalid': invalid_count,
            'results': results
        }


if __name__ == '__main__':
    # テスト用コード
    import sys

    print("=== YouTube Shorts 動画検証テスト ===\n")

    # ffprobeのチェック
    if ShortsValidator.check_ffprobe_installed():
        print("✓ ffprobeがインストールされています")
    else:
        print("✗ ffprobeがインストールされていません")
        print("動画の検証を行うには、ffmpegをインストールしてください")
        sys.exit(1)

    # 使用例
    print("\n使用例:")
    print("1. 単一ファイルの検証:")
    print("   result, specs = ShortsValidator.check_video_specs('video.mp4')")
    print("   ShortsValidator.print_validation_result('video.mp4', result, specs)")
    print("\n2. ディレクトリ内の全ファイルを検証:")
    print("   ShortsValidator.validate_directory('shorts_videos')")
