import pandas as pd
import numpy as np
import ta
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """技术分析指标计算器"""
    
    def __init__(self):
        pass
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> Dict:
        """计算所有技术指标"""
        if df is None or df.empty:
            return {}
        
        try:
            indicators = {}
            
            # 趋势指标
            indicators.update(self.calculate_trend_indicators(df))
            
            # 动量指标
            indicators.update(self.calculate_momentum_indicators(df))
            
            # 波动性指标
            indicators.update(self.calculate_volatility_indicators(df))
            
            # 成交量指标
            indicators.update(self.calculate_volume_indicators(df))
            
            # 支撑阻力位
            indicators.update(self.calculate_support_resistance(df))
            
            return indicators
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return {}
    
    def calculate_trend_indicators(self, df: pd.DataFrame) -> Dict:
        """计算趋势指标"""
        indicators = {}
        
        try:
            # 移动平均线
            indicators['sma_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            indicators['sma_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            indicators['ema_12'] = ta.trend.ema_indicator(df['Close'], window=12)
            indicators['ema_26'] = ta.trend.ema_indicator(df['Close'], window=26)
            
            # MACD
            macd_line = ta.trend.macd_diff(df['Close'])
            macd_signal = ta.trend.macd_signal(df['Close'])
            macd_histogram = ta.trend.macd(df['Close'])
            
            indicators['macd_line'] = macd_line
            indicators['macd_signal'] = macd_signal
            indicators['macd_histogram'] = macd_histogram
            
            # 当前MACD状态
            if not macd_line.empty and not macd_signal.empty:
                current_macd = macd_line.iloc[-1]
                current_signal = macd_signal.iloc[-1]
                indicators['macd_status'] = 'bullish' if current_macd > current_signal else 'bearish'
            
            # ADX (趋势强度)
            indicators['adx'] = ta.trend.adx(df['High'], df['Low'], df['Close'])
            
            # 布林带
            bb_high = ta.volatility.bollinger_hband(df['Close'])
            bb_low = ta.volatility.bollinger_lband(df['Close'])
            bb_mid = ta.volatility.bollinger_mavg(df['Close'])
            
            indicators['bb_upper'] = bb_high
            indicators['bb_lower'] = bb_low
            indicators['bb_middle'] = bb_mid
            
            # 布林带位置
            if not bb_high.empty and not bb_low.empty:
                current_price = df['Close'].iloc[-1]
                current_upper = bb_high.iloc[-1]
                current_lower = bb_low.iloc[-1]
                
                if current_price > current_upper:
                    indicators['bb_position'] = 'above_upper'
                elif current_price < current_lower:
                    indicators['bb_position'] = 'below_lower'
                else:
                    indicators['bb_position'] = 'within_bands'
            
        except Exception as e:
            logger.error(f"计算趋势指标失败: {e}")
        
        return indicators
    
    def calculate_momentum_indicators(self, df: pd.DataFrame) -> Dict:
        """计算动量指标"""
        indicators = {}
        
        try:
            # RSI
            rsi = ta.momentum.rsi(df['Close'])
            indicators['rsi'] = rsi
            
            if not rsi.empty:
                current_rsi = rsi.iloc[-1]
                if current_rsi > 70:
                    indicators['rsi_status'] = 'overbought'
                elif current_rsi < 30:
                    indicators['rsi_status'] = 'oversold'
                else:
                    indicators['rsi_status'] = 'neutral'
            
            # 随机指标 (KDJ)
            stoch_k = ta.momentum.stoch(df['High'], df['Low'], df['Close'])
            stoch_d = ta.momentum.stoch_signal(df['High'], df['Low'], df['Close'])
            
            indicators['stoch_k'] = stoch_k
            indicators['stoch_d'] = stoch_d
            
            # Williams %R
            indicators['williams_r'] = ta.momentum.williams_r(df['High'], df['Low'], df['Close'])
            
            # CCI (商品通道指数)
            indicators['cci'] = ta.trend.cci(df['High'], df['Low'], df['Close'])
            
        except Exception as e:
            logger.error(f"计算动量指标失败: {e}")
        
        return indicators
    
    def calculate_volatility_indicators(self, df: pd.DataFrame) -> Dict:
        """计算波动性指标"""
        indicators = {}
        
        try:
            # ATR (平均真实波幅)
            indicators['atr'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'])
            
            # 历史波动率
            returns = df['Close'].pct_change().dropna()
            if len(returns) > 1:
                indicators['historical_volatility'] = returns.std() * np.sqrt(252) * 100  # 年化波动率
            
            # 价格变化率
            indicators['price_change_pct'] = df['Close'].pct_change() * 100
            
        except Exception as e:
            logger.error(f"计算波动性指标失败: {e}")
        
        return indicators
    
    def calculate_volume_indicators(self, df: pd.DataFrame) -> Dict:
        """计算成交量指标"""
        indicators = {}
        
        try:
            # 成交量移动平均
            indicators['volume_sma'] = ta.volume.volume_sma(df['Close'], df['Volume'])
            
            # OBV (能量潮)
            indicators['obv'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])
            
            # 成交量价格趋势 (VPT)
            indicators['vpt'] = ta.volume.volume_price_trend(df['Close'], df['Volume'])
            
            # 资金流量指数 (MFI)
            indicators['mfi'] = ta.volume.money_flow_index(df['High'], df['Low'], df['Close'], df['Volume'])
            
        except Exception as e:
            logger.error(f"计算成交量指标失败: {e}")
        
        return indicators
    
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict:
        """计算支撑阻力位"""
        indicators = {}
        
        try:
            if len(df) < window:
                return indicators
            
            # 使用滚动窗口找局部高低点
            highs = df['High'].rolling(window=window, center=True).max()
            lows = df['Low'].rolling(window=window, center=True).min()
            
            # 找出支撑位和阻力位
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(df) - window):
                if df['High'].iloc[i] == highs.iloc[i]:
                    resistance_levels.append(df['High'].iloc[i])
                if df['Low'].iloc[i] == lows.iloc[i]:
                    support_levels.append(df['Low'].iloc[i])
            
            # 去重并排序
            resistance_levels = sorted(list(set(resistance_levels)), reverse=True)[:5]
            support_levels = sorted(list(set(support_levels)))[:5]
            
            indicators['resistance_levels'] = resistance_levels
            indicators['support_levels'] = support_levels
            
            # 当前价格相对位置
            current_price = df['Close'].iloc[-1]
            if resistance_levels:
                nearest_resistance = min(resistance_levels, key=lambda x: abs(x - current_price) if x > current_price else float('inf'))
                if nearest_resistance != float('inf'):
                    indicators['nearest_resistance'] = nearest_resistance
            
            if support_levels:
                nearest_support = max(support_levels, key=lambda x: x if x < current_price else 0)
                if nearest_support > 0:
                    indicators['nearest_support'] = nearest_support
            
        except Exception as e:
            logger.error(f"计算支撑阻力位失败: {e}")
        
        return indicators
    
    def get_trading_signals(self, indicators: Dict) -> Dict:
        """基于技术指标生成交易信号"""
        signals = {
            'overall_signal': 'neutral',
            'signal_strength': 0,
            'signals': []
        }
        
        try:
            signal_count = 0
            total_signals = 0
            
            # RSI信号
            if 'rsi_status' in indicators:
                total_signals += 1
                if indicators['rsi_status'] == 'oversold':
                    signals['signals'].append('RSI超卖，可能反弹')
                    signal_count += 1
                elif indicators['rsi_status'] == 'overbought':
                    signals['signals'].append('RSI超买，可能回调')
                    signal_count -= 1
            
            # MACD信号
            if 'macd_status' in indicators:
                total_signals += 1
                if indicators['macd_status'] == 'bullish':
                    signals['signals'].append('MACD金叉，趋势向好')
                    signal_count += 1
                else:
                    signals['signals'].append('MACD死叉，趋势转弱')
                    signal_count -= 1
            
            # 布林带信号
            if 'bb_position' in indicators:
                total_signals += 1
                if indicators['bb_position'] == 'below_lower':
                    signals['signals'].append('价格跌破布林带下轨，超卖')
                    signal_count += 1
                elif indicators['bb_position'] == 'above_upper':
                    signals['signals'].append('价格突破布林带上轨，超买')
                    signal_count -= 1
            
            # 计算总体信号
            if total_signals > 0:
                signal_ratio = signal_count / total_signals
                signals['signal_strength'] = signal_ratio
                
                if signal_ratio > 0.3:
                    signals['overall_signal'] = 'bullish'
                elif signal_ratio < -0.3:
                    signals['overall_signal'] = 'bearish'
                else:
                    signals['overall_signal'] = 'neutral'
            
        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
        
        return signals
    
    def format_indicators_summary(self, indicators: Dict) -> str:
        """格式化技术指标摘要"""
        try:
            summary_lines = []
            
            # RSI
            if 'rsi' in indicators and not indicators['rsi'].empty:
                current_rsi = indicators['rsi'].iloc[-1]
                rsi_status = indicators.get('rsi_status', 'neutral')
                summary_lines.append(f"RSI: {current_rsi:.2f} ({rsi_status})")
            
            # MACD
            if 'macd_line' in indicators and not indicators['macd_line'].empty:
                current_macd = indicators['macd_line'].iloc[-1]
                macd_status = indicators.get('macd_status', 'neutral')
                summary_lines.append(f"MACD: {current_macd:.4f} ({macd_status})")
            
            # 布林带
            if 'bb_position' in indicators:
                bb_position = indicators['bb_position']
                summary_lines.append(f"布林带位置: {bb_position}")
            
            # 支撑阻力
            if 'nearest_support' in indicators:
                support = indicators['nearest_support']
                summary_lines.append(f"最近支撑位: {support:.2f}")
            
            if 'nearest_resistance' in indicators:
                resistance = indicators['nearest_resistance']
                summary_lines.append(f"最近阻力位: {resistance:.2f}")
            
            return "\n".join(summary_lines) if summary_lines else "暂无技术指标数据"
            
        except Exception as e:
            logger.error(f"格式化指标摘要失败: {e}")
            return "技术指标计算出错"