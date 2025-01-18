# 暗号通貨分析ツール

このツールは、ビットコインのアドレス保有状況と主要な暗号通貨の価格推移を分析・可視化するためのPythonスクリプトです。

## セットアップ

1. 仮想環境の作成と有効化:
```bash
uv venv
source .venv/bin/activate  # Unix/macOS
# または
.venv\Scripts\activate     # Windows
```

2. 必要なライブラリをインストール:
```bash
uv pip install --upgrade pip
uv pip install -r requirements.txt
```

## 使用方法

1. スクリプトを実行:
```bash
python crypto_analysis.py
```

スクリプトは以下の処理を行います：
- ビットコインの10,000BTC以上を保有するアドレス数のデータを取得
- BTC、DOGE、XMRの価格データをYahoo Financeから取得
- 4つのグラフを含む分析チャートを生成
- 結果を`crypto_analysis.png`として保存

## 出力

スクリプトは以下の4つのグラフを含む画像ファイルを生成します：
1. 10,000BTC以上を保有するアドレス数の推移
2. ビットコイン価格の推移（1000USD単位）
3. Dogecoin価格の推移
4. Monero価格の推移 