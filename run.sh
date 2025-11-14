#!/bin/bash

# 仮想環境が存在するか確認
if [ ! -d "venv" ]; then
    echo "エラー: 仮想環境が見つかりません。"
    echo "先にsetup.shを実行してセットアップを完了してください。"
    exit 1
fi

# 仮想環境を有効化してスクリプトを実行
source venv/bin/activate
python main.py "$@"

# 仮想環境を無効化
deactivate
