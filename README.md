# Bitcoin Market Analysis Tool

ビットコイン市場の包括的な分析を行うためのツールです。価格データ、オンチェーン指標、市場センチメント、相関分析など、複数の指標を組み合わせて市場トレンドを分析します。

## 機能

- 複数の指標の自動データ収集と可視化
- 既存データの確認と必要なデータのみの取得
- 休場日（週末・祝日）のスキップ
- テクニカル指標の自動計算（RSI、MACD、移動平均）
- 相関分析（DXY、S&P500、Gold）
- ETFフロー分析
- グラフの自動生成と保存
- 5段階市場シグナル表示（背景色による直感的な判断支援）

## 収集する指標

### 価格指標
- BTCUSD価格データ
- 移動平均（21日、50日、200日）
- RSI（14日）
- MACD

### 相関指標
- DXY（米ドル指数）相関
- S&P500相関
- Gold相関

### オンチェーン指標
- 大口保有者データ
- アクティブアドレス数
- ハッシュレート

### 市場指標
- Fear & Greedインデックス
- ファンディングレート
- オープンインタレスト
- 取引量
- ETFフロー（GBTC、BITO）
- Googleトレンド（bitcoin、BTC、crypto）

## 市場シグナル

価格チャートの背景色で市場シグナルを5段階で表示します：

- 濃い緑色：強い買いシグナル
- 薄い緑色：買いシグナル
- グレー：中立
- 薄い赤色：売りシグナル
- 濃い赤色：強い売りシグナル

シグナルは以下の指標を組み合わせて算出されます：

1. RSI（重み：1.0）
   - 30以下：買い
   - 70以上：売り

2. MACD（重み：1.5）
   - ゴールデンクロス：買い
   - デッドクロス：売り

3. 移動平均（重み：2.0）
   - 200日MAの上：買い
   - 200日MAの下：売り

4. Fear & Greedインデックス（重み：0.5）
   - 25以下：買い
   - 75以上：売り

## セットアップ

1. リポジトリのクローン:
```bash
git clone https://github.com/Akira-Osanai/bitcoin-market-analyzer.git
cd bitcoin-market-analyzer
```

2. 仮想環境の作成と有効化:
```bash
python -m venv venv
source .venv/bin/activate  # Unix/macOS
# または
.\venv\Scripts\activate  # Windows
```

3. 依存パッケージのインストール:
```bash
pip install -r requirements.txt
```

## 使用方法

1. スクリプトの実行:
```bash
python crypto_analysis.py
```

2. 出力ファイル:
- 各指標のCSVファイルが `market_data/` ディレクトリに保存されます
- グラフは `crypto_analysis.png` として保存されます

## Dockerでの実行

Docker 環境での実行方法です。ローカルに Python を用意せずに動かせますわ🌙

1. 画像のビルド:
```bash
docker compose build
```

2. 実行（単発ジョブ）:
```bash
docker compose run --rm analyzer
```

3. 出力:
- `market_data/` に各種 CSV が保存されます（ホストにマウントされます）
- `crypto_analysis.png` がプロジェクト直下に保存されます

補足:
- ヘッドレス描画のため `MPLBACKEND=Agg` を使用しています
- ネットワーク経由で外部 API にアクセスしますので、環境のネットワーク制限にご注意ください

## 定期実行（cron）

このリポジトリには、毎日自動で実行するためのセットアップスクリプトを用意していますわ。

1. セットアップ（毎日 06:00 実行）
```bash
chmod +x ./setup.sh
./setup.sh
```

2. 実行時間を変更（例: 毎日 03:30）
```bash
SCHEDULE="30 3 * * *" ./setup.sh
```

3. 手動テスト（cron と同じ処理を即時実行）
```bash
./scripts/run_daily.sh
```

4. ログ
- 実行ログは `logs/cron.log` に追記されます

5. macOS で crontab 登録に失敗する場合（Operation not permitted）
- 設定 > プライバシーとセキュリティ > フルディスクアクセス にて `Terminal` と `/usr/sbin/cron` を追加し、再度 `./setup.sh` を実行
- あるいは root の crontab に登録します:
```bash
sudo SCHEDULE="0 6 * * *" ./setup.sh
```

## データ更新

- スクリプトは既存のCSVファイルをチェックし、必要な期間のデータのみを取得します
- 週末や祝日のデータは自動的にスキップされます
- 各APIの制限に応じて適切な待機時間が設定されています

## 分析ガイド

詳細な市場分析の方法については、[ANALYSIS_GUIDE.md](ANALYSIS_GUIDE.md)を参照してください。

## 注意事項

- CSVファイルはGitの管理対象外です（.gitignoreに設定済み）
- 一部のデータ取得にはAPIキーが必要な場合があります
- 投資判断は自己責任で行ってください

## ライセンス

MIT License

## プロジェクト構造

```
bitcoin-market-analyzer/
├── crypto_analysis.py      # メインスクリプト
├── requirements.txt        # 依存パッケージ
├── README.md              # プロジェクト説明
├── ANALYSIS_GUIDE.md      # 分析ガイド
└── util/
    ├── data_collector.py   # データ収集メインクラス
    ├── plot_market_data.py # プロット機能のエントリーポイント
    ├── collectors/        # データ収集モジュール
    │   ├── base_collector.py
    │   ├── market_data.py
    │   ├── onchain_data.py
    │   ├── derivative_data.py
    │   ├── sentiment_data.py
    │   ├── exchange_data.py
    │   └── etf_data.py
    └── plotters/          # プロット機能モジュール
        ├── base_plotter.py
        ├── technical_indicators.py
        ├── correlation_plotter.py
        └── market_plotter.py
```

### モジュール説明

#### データ収集モジュール
- `base_collector.py`: 基本的なデータ収集機能
- `market_data.py`: 価格データの収集（BTCUSD、DXY、S&P500、Gold）
- `onchain_data.py`: オンチェーンデータの収集
- `derivative_data.py`: デリバティブデータの収集
- `sentiment_data.py`: センチメントデータの収集
- `exchange_data.py`: 取引所データの収集
- `etf_data.py`: ETFデータの収集

#### プロットモジュール
- `base_plotter.py`: 基本的なプロット設定、グリッド作成、軸フォーマット、カラーパレット
- `technical_indicators.py`: テクニカル指標（RSI、移動平均線、MACD）の計算
- `correlation_plotter.py`: 相関分析のプロット
- `market_plotter.py`: メインのプロット機能
  - BTCUSDのメインチャート
  - 各種指標のサブチャート
  - BTCUSDの参照線（各サブチャートに表示）
  - ボーダーライン（各指標の重要レベル）

### 主な機能
1. データ収集
   - BTCUSDの価格データ
   - 移動平均（21日、50日、200日）
   - RSI（14日）
   - MACD
   - 他資産との相関分析（DXY、S&P500、Gold）
   - オンチェーンデータの分析（大口保有者データ、アクティブアドレス数、ハッシュレート）
   - センチメントデータの分析（Fear & Greedインデックス）
   - 取引所データの分析（取引量、ETFフロー）
   - ファンディングレート
   - オープンインタレスト
   - Googleトレンド

2. データ分析・可視化
   - BTCUSDの価格推移と主要な移動平均線
   - テクニカル指標（RSI、MACD）
   - 他資産との相関分析
   - オンチェーンデータの分析
   - 各指標とBTCUSDの価格推移の関係を視覚的に確認可能（参照線機能）