from .collectors.base_collector import BaseCollector
from .collectors.market_data import MarketDataCollector
from .collectors.onchain_data import OnchainDataCollector
from .collectors.derivative_data import DerivativeDataCollector
from .collectors.sentiment_data import SentimentDataCollector
from .collectors.exchange_data import ExchangeDataCollector
from .collectors.etf_data import ETFDataCollector

class DataCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.market_collector = MarketDataCollector()
        self.onchain_collector = OnchainDataCollector()
        self.derivative_collector = DerivativeDataCollector()
        self.sentiment_collector = SentimentDataCollector()
        self.exchange_collector = ExchangeDataCollector()
        self.etf_collector = ETFDataCollector()

    def collect_all_data(self):
        """全てのデータを収集します。"""
        results = {}
        print("="*50)
        print("データ収集を開始...")
        print(f"期間: {self.start_date.strftime('%Y-%m-%d')} から {self.end_date.strftime('%Y-%m-%d')}")
        print("="*50)
        
        # 市場データ
        results['btcusd'] = self.market_collector.get_btcusd_data()
        results['dxy'] = self.market_collector.get_dxy_data()
        results['sp500'] = self.market_collector.get_sp500_data()
        results['gold'] = self.market_collector.get_gold_data()
        
        # オンチェーンデータ
        results['large_holders'] = self.onchain_collector.get_large_holders_data()
        results['active_addresses'] = self.onchain_collector.get_active_addresses()
        results['hash_rate'] = self.onchain_collector.get_hash_rate()
        
        # デリバティブデータ
        results['funding_rates'] = self.derivative_collector.get_funding_rates()
        results['open_interest'] = self.derivative_collector.get_open_interest()
        
        # センチメントデータ
        results['fear_greed'] = self.sentiment_collector.get_fear_greed_index()
        results['google_trends'] = self.sentiment_collector.get_google_trends_data()
        
        # 取引所データ
        results['trading_volume'] = self.exchange_collector.get_trading_volume()
        results['coinbase_premium'] = self.exchange_collector.get_coinbase_premium()
        
        # ETFデータ
        results['etf'] = self.etf_collector.get_etf_data()
        
        success_count = sum(1 for v in results.values() if v is not None)
        total_count = len(results)
        
        print("\n" + "="*50)
        print(f"データ収集完了: {success_count}/{total_count} 成功")
        print("="*50)
        return results if success_count > 0 else None