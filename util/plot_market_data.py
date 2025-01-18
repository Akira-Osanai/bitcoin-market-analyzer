from .plotters.market_plotter import MarketPlotter

def plot_market_data(results):
    """市場データをプロット
    
    Args:
        results (dict): 各種市場データを含む辞書
    """
    plotter = MarketPlotter()
    plotter.plot_market_data(results)