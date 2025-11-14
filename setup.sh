#!/bin/bash

echo "========================================"
echo "YouTube Shorts Uploader セットアップ"
echo "========================================"
echo ""

# Pythonがインストールされているか確認
if ! command -v python3 &> /dev/null; then
    echo "エラー: Python3がインストールされていません。"
    echo "Python 3.7以上をインストールしてください。"
    exit 1
fi

echo "✓ Pythonが見つかりました"
python3 --version
echo ""

# 仮想環境が存在するか確認
if [ -d "venv" ]; then
    echo "仮想環境は既に存在します。"
    read -p "仮想環境を再作成しますか？ (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "既存の仮想環境を削除しています..."
        rm -rf venv
    else
        echo "既存の仮想環境を使用します。"
        SKIP_VENV_CREATION=1
    fi
fi

# 仮想環境を作成
if [ -z "$SKIP_VENV_CREATION" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "エラー: 仮想環境の作成に失敗しました。"
        exit 1
    fi
    echo "✓ 仮想環境を作成しました"
    echo ""
fi

# 仮想環境を有効化して依存パッケージをインストール
echo "依存パッケージをインストールしています..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "エラー: 依存パッケージのインストールに失敗しました。"
    exit 1
fi
echo "✓ 依存パッケージをインストールしました"
echo ""

# ffmpegのチェック
echo "Checking for ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "[WARNING] ffmpeg is not installed."
    echo ""
    echo "ffmpeg is required for video validation."
    echo ""
    echo "Installation options:"

    # OSの判定
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Ubuntu/Debian:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install ffmpeg"
        echo ""
        echo "Fedora/RHEL:"
        echo "  sudo dnf install ffmpeg"
        echo ""

        # 自動インストールを試みる
        read -p "Do you want to install ffmpeg automatically? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v apt-get &> /dev/null; then
                echo "Installing ffmpeg via apt-get..."
                sudo apt-get update && sudo apt-get install -y ffmpeg
                if [ $? -eq 0 ]; then
                    echo "[OK] ffmpeg installed successfully"
                else
                    echo "[WARNING] ffmpeg installation failed"
                fi
            elif command -v dnf &> /dev/null; then
                echo "Installing ffmpeg via dnf..."
                sudo dnf install -y ffmpeg
                if [ $? -eq 0 ]; then
                    echo "[OK] ffmpeg installed successfully"
                else
                    echo "[WARNING] ffmpeg installation failed"
                fi
            else
                echo "Package manager not detected. Please install manually."
            fi
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS:"
        echo "  brew install ffmpeg"
        echo ""

        # Homebrewが利用可能かチェック
        if command -v brew &> /dev/null; then
            read -p "Do you want to install ffmpeg using Homebrew? (y/N): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "Installing ffmpeg via Homebrew..."
                brew install ffmpeg
                if [ $? -eq 0 ]; then
                    echo "[OK] ffmpeg installed successfully"
                else
                    echo "[WARNING] ffmpeg installation failed"
                fi
            fi
        fi
    fi

    echo ""
    echo "Note: You can skip validation using --skip-validation option"
    echo ""
else
    echo "[OK] ffmpeg found"
    ffmpeg -version 2>&1 | head -n 1
    echo ""
fi

# client_secretファイルの確認
if ! ls client_secret*.json 1> /dev/null 2>&1; then
    echo "⚠ 警告: client_secretファイルが見つかりません。"
    echo ""
    echo "Google Cloud Consoleから以下の手順でOAuth認証情報をダウンロードしてください:"
    echo "1. https://console.cloud.google.com/ にアクセス"
    echo "2. プロジェクトを選択"
    echo "3. 「APIとサービス」→「認証情報」"
    echo "4. OAuth 2.0クライアントIDをダウンロード"
    echo "5. ダウンロードしたJSONファイルをこのディレクトリに配置"
    echo ""
else
    echo "✓ client_secretファイルが見つかりました"
    echo ""
fi

# ディレクトリ構造の確認
mkdir -p shorts_videos logs
echo "✓ 必要なディレクトリを作成しました"
echo ""

echo "========================================"
echo "セットアップが完了しました！"
echo "========================================"
echo ""
echo "次のステップ:"
echo ""
echo "1. client_secretファイルがない場合は配置してください"
echo ""
echo "2. 認証を実行:"
echo "   source venv/bin/activate"
echo "   python main.py auth --show-info"
echo ""
echo "3. 動画をアップロード:"
echo "   python main.py upload shorts_videos/video.mp4 -t \"タイトル\""
echo ""
echo "詳細はREADME.mdを参照してください。"
echo ""
