from util.data_collector import DataCollector
from util.plot_market_data import plot_market_data


def main():
    print("暗号通貨データの収集と分析を開始します...")
    collector = DataCollector()
    results = collector.collect_all_data()
    
    if results:
        plot_market_data(results)
    else:
        print("データ収集に失敗したため、分析を実行できません")

if __name__ == "__main__":
    main() 