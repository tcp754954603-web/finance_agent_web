from typing import Dict, Optional
import pandas as pd
from .technical_indicators import TechnicalAnalyzer
import logging

logger = logging.getLogger(__name__)


class EnhancedLLMReasoner:
    """增强的LLM分析器，结合技术指标和基本面分析"""
    
    def __init__(self):
        self.technical_analyzer = TechnicalAnalyzer()
    
    def comprehensive_analysis(self, symbol: str, df: pd.DataFrame, stock_info: Dict = None, 
                             model_name: str = "qwen2.5") -> str:
        """综合分析股票，包含技术面、基本面和AI推理"""
        
        if df is None or df.empty:
            return "没有足够的数据进行分析。"
        
        try:
            # 1. 基础价格分析
            price_summary = self._analyze_price_action(df)
            
            # 2. 技术指标分析
            technical_indicators = self.technical_analyzer.calculate_all_indicators(df)
            technical_summary = self.technical_analyzer.format_indicators_summary(technical_indicators)
            trading_signals = self.technical_analyzer.get_trading_signals(technical_indicators)
            
            # 3. 基本面信息
            fundamental_summary = self._format_fundamental_info(stock_info) if stock_info else ""
            
            # 4. 构建详细的分析提示词
            analysis_prompt = self._build_analysis_prompt(
                symbol, price_summary, technical_summary, 
                trading_signals, fundamental_summary
            )
            
            # 5. 调用LLM进行综合分析
            llm_analysis = self._call_llm_analysis(analysis_prompt, model_name)
            
            return llm_analysis
            
        except Exception as e:
            logger.error(f"综合分析失败: {e}")
            return f"分析过程中出现错误: {str(e)}"
    
    def _analyze_price_action(self, df: pd.DataFrame, lookback_days: int = 30) -> Dict:
        """分析价格走势"""
        try:
            if len(df) < lookback_days:
                lookback_days = len(df)
            
            recent_data = df.tail(lookback_days)
            
            start_price = float(recent_data['Close'].iloc[0])
            end_price = float(recent_data['Close'].iloc[-1])
            max_price = float(recent_data['High'].max())
            min_price = float(recent_data['Low'].min())
            avg_volume = float(recent_data['Volume'].mean())
            
            change = end_price - start_price
            change_pct = (change / start_price * 100) if start_price != 0 else 0.0
            
            # 计算波动率
            returns = recent_data['Close'].pct_change().dropna()
            volatility = returns.std() * 100 if len(returns) > 1 else 0
            
            # 趋势判断
            if change_pct > 5:
                trend = "强势上涨"
            elif change_pct > 1:
                trend = "温和上涨"
            elif change_pct > -1:
                trend = "横盘整理"
            elif change_pct > -5:
                trend = "温和下跌"
            else:
                trend = "大幅下跌"
            
            return {
                'start_price': start_price,
                'end_price': end_price,
                'max_price': max_price,
                'min_price': min_price,
                'change': change,
                'change_pct': change_pct,
                'volatility': volatility,
                'avg_volume': avg_volume,
                'trend': trend,
                'lookback_days': lookback_days
            }
            
        except Exception as e:
            logger.error(f"价格分析失败: {e}")
            return {}
    
    def _format_fundamental_info(self, stock_info: Dict) -> str:
        """格式化基本面信息"""
        try:
            if not stock_info or 'error' in stock_info:
                return ""
            
            lines = []
            lines.append(f"公司名称: {stock_info.get('name', 'N/A')}")
            lines.append(f"行业: {stock_info.get('sector', 'N/A')} - {stock_info.get('industry', 'N/A')}")
            
            market_cap = stock_info.get('market_cap', 0)
            if market_cap > 0:
                if market_cap > 1e12:
                    cap_str = f"{market_cap/1e12:.2f}万亿"
                elif market_cap > 1e9:
                    cap_str = f"{market_cap/1e9:.2f}十亿"
                else:
                    cap_str = f"{market_cap/1e6:.2f}百万"
                lines.append(f"市值: {cap_str} {stock_info.get('currency', 'USD')}")
            
            pe_ratio = stock_info.get('pe_ratio', 0)
            if pe_ratio > 0:
                lines.append(f"市盈率: {pe_ratio:.2f}")
            
            dividend_yield = stock_info.get('dividend_yield', 0)
            if dividend_yield > 0:
                lines.append(f"股息率: {dividend_yield*100:.2f}%")
            
            beta = stock_info.get('beta', 0)
            if beta > 0:
                lines.append(f"Beta系数: {beta:.2f}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"格式化基本面信息失败: {e}")
            return ""
    
    def _build_analysis_prompt(self, symbol: str, price_summary: Dict, 
                              technical_summary: str, trading_signals: Dict, 
                              fundamental_summary: str) -> str:
        """构建分析提示词"""
        
        prompt = f"""你是一位资深的证券分析师，请对股票 {symbol} 进行全面的投资分析。

## 基本信息
{fundamental_summary}

## 价格走势分析（最近{price_summary.get('lookback_days', 30)}个交易日）
- 起始价格: ${price_summary.get('start_price', 0):.2f}
- 最新价格: ${price_summary.get('end_price', 0):.2f}
- 涨跌幅: {price_summary.get('change_pct', 0):.2f}%
- 最高价: ${price_summary.get('max_price', 0):.2f}
- 最低价: ${price_summary.get('min_price', 0):.2f}
- 价格波动率: {price_summary.get('volatility', 0):.2f}%
- 趋势判断: {price_summary.get('trend', '未知')}
- 平均成交量: {price_summary.get('avg_volume', 0):,.0f}

## 技术指标分析
{technical_summary}

## 交易信号
- 总体信号: {trading_signals.get('overall_signal', 'neutral')}
- 信号强度: {trading_signals.get('signal_strength', 0):.2f}
- 具体信号: {', '.join(trading_signals.get('signals', []))}

请基于以上信息，从以下几个维度进行分析：

1. **技术面分析**: 结合各项技术指标，判断当前的技术形态和趋势方向
2. **风险评估**: 分析当前的投资风险，包括技术风险和市场风险
3. **投资建议**: 给出具体的投资建议和操作策略
4. **关键价位**: 指出重要的支撑位和阻力位
5. **风险提示**: 提醒投资者需要注意的风险点

要求：
- 使用专业但易懂的语言
- 结构清晰，分点论述
- 不要给出具体的买入/卖出价格建议
- 强调风险管理的重要性
- 使用中文回答"""

        return prompt
    
    def _call_llm_analysis(self, prompt: str, model_name: str) -> str:
        """调用LLM进行分析"""
        try:
            from langchain_ollama import ChatOllama
            
            llm = ChatOllama(model=model_name, temperature=0.3)
            response = llm.invoke(prompt)
            
            content = getattr(response, "content", None)
            if content is None:
                content = str(response)
            
            return content
            
        except ImportError:
            return "LLM分析功能需要安装 langchain-ollama 依赖包。请运行: pip install langchain-ollama"
        except Exception as e:
            logger.error(f"LLM分析调用失败: {e}")
            return f"AI分析暂时不可用: {str(e)}\n\n请确认 Ollama 服务正在运行，并已安装模型 {model_name}。"
    
    def quick_analysis(self, symbol: str, df: pd.DataFrame) -> str:
        """快速分析（不使用LLM）"""
        try:
            if df is None or df.empty:
                return "没有足够的数据进行分析。"
            
            # 价格分析
            price_summary = self._analyze_price_action(df)
            
            # 技术指标
            technical_indicators = self.technical_analyzer.calculate_all_indicators(df)
            trading_signals = self.technical_analyzer.get_trading_signals(technical_indicators)
            
            # 构建快速分析报告
            report_lines = []
            report_lines.append(f"=== {symbol} 快速分析报告 ===\n")
            
            # 价格走势
            report_lines.append("📈 价格走势:")
            report_lines.append(f"  当前趋势: {price_summary.get('trend', '未知')}")
            report_lines.append(f"  涨跌幅: {price_summary.get('change_pct', 0):.2f}%")
            report_lines.append(f"  波动率: {price_summary.get('volatility', 0):.2f}%\n")
            
            # 技术信号
            report_lines.append("🔍 技术信号:")
            report_lines.append(f"  总体信号: {trading_signals.get('overall_signal', 'neutral')}")
            report_lines.append(f"  信号强度: {trading_signals.get('signal_strength', 0):.2f}")
            
            signals = trading_signals.get('signals', [])
            if signals:
                report_lines.append("  具体信号:")
                for signal in signals:
                    report_lines.append(f"    • {signal}")
            
            report_lines.append("\n⚠️ 风险提示:")
            report_lines.append("  • 技术分析仅供参考，不构成投资建议")
            report_lines.append("  • 投资有风险，请谨慎决策")
            report_lines.append("  • 建议结合基本面分析和市场环境综合判断")
            
            return "\n".join(report_lines)
            
        except Exception as e:
            logger.error(f"快速分析失败: {e}")
            return f"快速分析出现错误: {str(e)}"


# 向后兼容函数
def analyze_stock_with_llm(symbol: str, df: pd.DataFrame, model_name: str = "qwen2.5") -> str:
    """向后兼容的股票分析函数"""
    analyzer = EnhancedLLMReasoner()
    return analyzer.comprehensive_analysis(symbol, df, model_name=model_name)