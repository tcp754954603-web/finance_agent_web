import yfinance as yf
import pandas as pd
import requests
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedStockDataFetcher:
    """增强的股票数据获取器，支持多数据源和多时间框架"""
    
    def __init__(self):
        self.data_sources = {
            'yfinance': self._fetch_yfinance_data,
            'alpha_vantage': self._fetch_alpha_vantage_data,
        }
    
    def get_stock_data(self, symbol: str, period: str = "1mo", interval: str = "1d", 
                      source: str = "yfinance", **kwargs) -> Optional[pd.DataFrame]:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 数据间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            source: 数据源 (yfinance, alpha_vantage)
        """
        try:
            if source in self.data_sources:
                return self.data_sources[source](symbol, period, interval, **kwargs)
            else:
                logger.warning(f"不支持的数据源: {source}，使用默认yfinance")
                return self._fetch_yfinance_data(symbol, period, interval)
        except Exception as e:
            logger.error(f"获取股票数据失败 {symbol}: {e}")
            return None
    
    def _fetch_yfinance_data(self, symbol: str, period: str, interval: str, **kwargs) -> Optional[pd.DataFrame]:
        """使用yfinance获取数据"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"yfinance未返回数据: {symbol}")
                return None
            
            # 标准化列名
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]  # 只保留OHLCV数据
            
            logger.info(f"成功获取 {symbol} 数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"yfinance获取数据失败 {symbol}: {e}")
            return None
    
    def _fetch_alpha_vantage_data(self, symbol: str, period: str, interval: str, **kwargs) -> Optional[pd.DataFrame]:
        """使用Alpha Vantage获取数据（保持向后兼容）"""
        api_key = kwargs.get('api_key')
        base_url = kwargs.get('base_url', 'https://www.alphavantage.co/query')
        
        if not api_key:
            logger.error("Alpha Vantage需要API密钥")
            return None
        
        # 映射间隔参数
        interval_map = {
            '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '60m': '60min'
        }
        av_interval = interval_map.get(interval, '5min')
        
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": av_interval,
            "apikey": api_key,
        }
        
        try:
            resp = requests.get(base_url, params=params, timeout=15)
            if resp.status_code != 200:
                logger.error(f"Alpha Vantage HTTP错误: {resp.status_code}")
                return None
            
            data = resp.json()
            key = f"Time Series ({av_interval})"
            
            if key not in data:
                logger.warning(f"Alpha Vantage返回数据异常: {data}")
                return None
            
            ts = data[key]
            df = pd.DataFrame.from_dict(ts, orient="index")
            df.columns = ["Open", "High", "Low", "Close", "Volume"]
            df.index = pd.to_datetime(df.index)
            
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            df = df.sort_index()
            logger.info(f"成功获取 {symbol} Alpha Vantage数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"Alpha Vantage获取数据失败 {symbol}: {e}")
            return None
    
    def get_stock_info(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键信息
            stock_info = {
                'symbol': symbol,
                'name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'price': info.get('currentPrice', 0),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'N/A'),
            }
            
            return stock_info
            
        except Exception as e:
            logger.error(f"获取股票信息失败 {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def get_multiple_stocks(self, symbols: List[str], period: str = "1mo", 
                           interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """批量获取多只股票数据"""
        results = {}
        
        for symbol in symbols:
            df = self.get_stock_data(symbol, period, interval)
            if df is not None:
                results[symbol] = df
            else:
                logger.warning(f"跳过无效股票: {symbol}")
        
        return results
    
    def get_market_indices(self) -> Dict[str, pd.DataFrame]:
        """获取主要市场指数数据"""
        indices = {
            'S&P 500': '^GSPC',
            'Dow Jones': '^DJI', 
            'NASDAQ': '^IXIC',
            'VIX': '^VIX',
            'Shanghai Composite': '000001.SS',
            'Hang Seng': '^HSI'
        }
        
        results = {}
        for name, symbol in indices.items():
            df = self.get_stock_data(symbol, period="1mo", interval="1d")
            if df is not None:
                results[name] = df
        
        return results


# 向后兼容的函数
def get_stock_data(symbol: str, api_key: str = None, base_url: str = None, 
                  period: str = "1mo", interval: str = "1d") -> Optional[pd.DataFrame]:
    """向后兼容的股票数据获取函数"""
    fetcher = EnhancedStockDataFetcher()
    
    if api_key:
        # 使用Alpha Vantage
        return fetcher.get_stock_data(symbol, period, interval, 'alpha_vantage', 
                                    api_key=api_key, base_url=base_url)
    else:
        # 使用yfinance
        return fetcher.get_stock_data(symbol, period, interval, 'yfinance')