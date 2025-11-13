from flask import Flask, render_template, request, jsonify
import yaml
import logging
import pandas as pd
from data_fetcher.enhanced_stock_data import EnhancedStockDataFetcher
from analysis.enhanced_llm_reasoner import EnhancedLLMReasoner
from analysis.technical_indicators import TechnicalAnalyzer

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 初始化组件
data_fetcher = EnhancedStockDataFetcher()
llm_analyzer = EnhancedLLMReasoner()
technical_analyzer = TechnicalAnalyzer()

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

alpha_cfg = config.get("alpha_vantage", {})
API_KEY = alpha_cfg.get("api_key", "")
BASE_URL = alpha_cfg.get("base_url", "https://www.alphavantage.co/query")

llm_cfg = config.get("llm", {})
LLM_ENABLE = bool(llm_cfg.get("enable", False))
LLM_MODEL = llm_cfg.get("model_name", "qwen2.5")

DEFAULT_SYMBOL = config.get("default_symbol", "AAPL")


@app.route("/")
def index():
    return render_template("index.html", default_symbol=DEFAULT_SYMBOL, llm_enabled=LLM_ENABLE)


@app.get("/api/stock")
def api_stock():
    symbol = request.args.get("symbol", "").strip().upper()
    if not symbol:
        return jsonify({"error": "缺少股票代码 symbol"}), 400

    if not API_KEY or API_KEY == "YOUR_ALPHA_VANTAGE_KEY":
        return jsonify({"error": "请先在 config.yaml 中配置 alpha_vantage.api_key"}), 500

    # 使用增强的数据获取器
    df = data_fetcher.get_stock_data(symbol, period="1mo", interval="5min", source='yfinance')
    if df is None:
        # 尝试使用Alpha Vantage作为备用
        if API_KEY and API_KEY != "YOUR_ALPHA_VANTAGE_KEY":
            df = data_fetcher.get_stock_data(symbol, period="1mo", interval="5min", source='alpha_vantage', 
                                           api_key=API_KEY, base_url=BASE_URL)
    
    if df is None or df.empty:
        return jsonify({"error": f"无法获取 {symbol} 的行情数据"}), 500

    first_row = df.iloc[0]
    last_row = df.iloc[-1]

    summary = {
        "symbol": symbol,
        "first_time": df.index[0].isoformat(),
        "last_time": df.index[-1].isoformat(),
        "first_close": float(first_row["Close"]),
        "last_close": float(last_row["Close"]),
        "change": float(last_row["Close"] - first_row["Close"]),
        "change_pct": float((last_row["Close"] - first_row["Close"]) / first_row["Close"] * 100)
        if first_row["Close"] != 0 else 0.0,
        "high": float(df["High"].max()),
        "low": float(df["Low"].min()),
    }

    points = [
        {"time": idx.isoformat(), "close": float(row["Close"])}
        for idx, row in df.iterrows()
    ]

    # 获取股票基本信息
    stock_info = data_fetcher.get_stock_info(symbol)
    
    # 技术分析
    technical_indicators = technical_analyzer.calculate_all_indicators(df)
    trading_signals = technical_analyzer.get_trading_signals(technical_indicators)
    
    analysis_text = None
    if LLM_ENABLE:
        try:
            analysis_text = llm_analyzer.comprehensive_analysis(symbol, df, stock_info, LLM_MODEL)
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            analysis_text = llm_analyzer.quick_analysis(symbol, df)
    else:
        analysis_text = llm_analyzer.quick_analysis(symbol, df)

    return jsonify({
        "summary": summary,
        "points": points,
        "llm_analysis": analysis_text,
        "stock_info": stock_info,
        "technical_summary": technical_analyzer.format_indicators_summary(technical_indicators),
        "trading_signals": trading_signals,
        "error": None,
    })


@app.route("/api/stock_data")
def api_stock_data():
    """新的增强API端点，支持更多参数和功能"""
    symbol = request.args.get("symbol", DEFAULT_SYMBOL)
    period = request.args.get("period", "1mo")
    interval = request.args.get("interval", "1d")
    analysis_type = request.args.get("analysis_type", "quick")  # quick, full, technical
    
    try:
        # 获取股票数据
        df = data_fetcher.get_stock_data(symbol, period, interval, 'yfinance')
        
        if df is None:
            # 尝试使用Alpha Vantage作为备用
            if API_KEY and API_KEY != "YOUR_ALPHA_VANTAGE_KEY":
                df = data_fetcher.get_stock_data(symbol, period, interval, 'alpha_vantage', 
                                               api_key=API_KEY, base_url=BASE_URL)
        
        if df is None:
            return jsonify({"error": "Failed to fetch stock data"}), 500
        
        # 获取股票基本信息
        stock_info = data_fetcher.get_stock_info(symbol)
        
        # 转换为前端需要的格式
        data = []
        for index, row in df.iterrows():
            data.append({
                "date": index.strftime("%Y-%m-%d %H:%M:%S") if hasattr(index, 'strftime') else str(index),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"])
            })
        
        # 技术指标分析
        technical_indicators = technical_analyzer.calculate_all_indicators(df)
        trading_signals = technical_analyzer.get_trading_signals(technical_indicators)
        
        # 分析结果
        analysis = ""
        if analysis_type == "technical":
            # 仅技术分析
            analysis = technical_analyzer.format_indicators_summary(technical_indicators)
        elif analysis_type == "quick":
            # 快速分析
            analysis = llm_analyzer.quick_analysis(symbol, df)
        elif analysis_type == "full" and LLM_ENABLE:
            # 完整AI分析
            try:
                analysis = llm_analyzer.comprehensive_analysis(symbol, df, stock_info, LLM_MODEL)
            except Exception as e:
                logger.error(f"LLM分析失败: {e}")
                analysis = llm_analyzer.quick_analysis(symbol, df)
        else:
            analysis = llm_analyzer.quick_analysis(symbol, df)
        
        # 构建响应
        response_data = {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": data,
            "analysis": analysis,
            "stock_info": stock_info,
            "technical_indicators": {
                "summary": technical_analyzer.format_indicators_summary(technical_indicators),
                "signals": trading_signals
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"API错误: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/market_overview")
def api_market_overview():
    """市场概览API"""
    try:
        indices = data_fetcher.get_market_indices()
        
        overview = {}
        for name, df in indices.items():
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                first = df.iloc[0]
                change = float(latest['Close'] - first['Close'])
                change_pct = float(change / first['Close'] * 100) if first['Close'] != 0 else 0
                
                overview[name] = {
                    "current_price": float(latest['Close']),
                    "change": change,
                    "change_pct": change_pct,
                    "high": float(df['High'].max()),
                    "low": float(df['Low'].min()),
                    "volume": int(df['Volume'].sum())
                }
        
        return jsonify({"market_overview": overview})
        
    except Exception as e:
        logger.error(f"市场概览API错误: {e}")
        return jsonify({"error": f"Failed to fetch market overview: {str(e)}"}), 500


if __name__ == "__main__":
    import sys
    
    # 解析命令行参数
    host = "0.0.0.0"
    port = 12000
    debug = True
    
    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
        elif arg == "--no-debug":
            debug = False
    
    # 如果没有命令行参数，使用配置文件
    if len(sys.argv) == 1:
        server_cfg = config.get("server", {})
        host = server_cfg.get("host", "127.0.0.1")
        port = int(server_cfg.get("port", 5000))
        debug = bool(server_cfg.get("debug", True))

    print(f"🚀 启动智能理财炒股 Agent 服务器...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    
    app.run(host=host, port=port, debug=debug)
