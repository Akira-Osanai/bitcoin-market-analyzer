# Bitcoin Market Analysis Tool

ビットコイン市場の包括的な分析を行うためのツールです。複数の指標を組み合わせて、市場動向を多角的に分析します。

## 機能

- 複数の指標の自動収集と可視化
- 既存データの確認と差分更新による効率的なデータ収集
- テクニカル指標（RSI、MACD、移動平均線）の計算と表示
- DXYとの相関分析
- グラフの自動生成と保存

## 収集する指標

1. BTCUSD価格データ
   - 21日、50日、200日の単純移動平均（SMA）
   - 21日、50日、200日の指数移動平均（EMA）
   - RSI（14日）
   - MACD（12,26,9）

2. 米ドル指数（DXY）
   - BTCUSDとの30日相関係数

3. オンチェーン指標
   - 大口保有者データ（10,000BTC以上）
   - アクティブアドレス数
   - ハッシュレート

4. 市場指標
   - ファンディングレート
   - Fear & Greed Index
   - オープンインタレスト
   - 取引量

## セットアップ

1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/bitcoin-market-analysis.git
cd bitcoin-market-analysis
```

2. 仮想環境の作成と有効化
```bash
python -m venv venv
source venv/bin/activate  # Linuxの場合
.\venv\Scripts\activate   # Windowsの場合
```

3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

## 使用方法

1. データの収集と分析
```bash
python crypto_analysis.py
```

2. 出力ファイル
- `market_data/`: 各指標のCSVファイル
  - `btcusd.csv`: BTCUSD価格データ
  - `dxy.csv`: 米ドル指数データ
  - `large_holders.csv`: 大口保有者データ
  - `funding_rates.csv`: ファンディングレート
  - `fear_greed.csv`: Fear & Greed Index
  - `open_interest.csv`: オープンインタレスト
  - `trading_volume.csv`: 取引量
  - `active_addresses.csv`: アクティブアドレス数
  - `hash_rate.csv`: ハッシュレート
- `crypto_analysis.png`: 分析結果のグラフ

## データ更新について

- 既存のCSVファイルがある場合、不足している期間のデータのみを取得
- 重複データは自動的に最新のものに更新
- CSVファイルはGitの管理対象外（.gitignoreに設定）

## 注意事項

- API制限に配慮して適切な間隔でデータを取得
- 一部のデータは取得できない日付が存在する可能性があります
- 投資判断は自己責任で行ってください

## ライセンス

MITライセンス