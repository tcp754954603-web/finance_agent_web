from flask import Flask, render_template, request, jsonify
import yaml
from data_fetcher.stock_data import get_stock_data
from analysis.llm_reasoner import analyze_stock_with_llm

app = Flask(__name__)

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

    df = get_stock_data(symbol, API_KEY, BASE_URL)
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

    analysis_text = None
    if LLM_ENABLE:
        analysis_text = analyze_stock_with_llm(symbol, df, model_name=LLM_MODEL)

    return jsonify({
        "summary": summary,
        "points": points,
        "llm_analysis": analysis_text,
        "error": None,
    })


if __name__ == "__main__":
    server_cfg = config.get("server", {})
    host = server_cfg.get("host", "127.0.0.1")
    port = int(server_cfg.get("port", 5000))
    debug = bool(server_cfg.get("debug", True))
    app.run(host=host, port=port, debug=debug)
