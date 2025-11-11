from typing import Dict
import pandas as pd


def summarize_price(df: pd.DataFrame, last_n: int = 30) -> Dict[str, float]:
    if df is None or df.empty:
        return {}

    tail = df.tail(last_n)
    start_price = float(tail["Close"].iloc[0])
    end_price = float(tail["Close"].iloc[-1])
    max_price = float(tail["Close"].max())
    min_price = float(tail["Close"].min())
    change = end_price - start_price
    change_pct = change / start_price * 100 if start_price != 0 else 0.0

    return {
        "start_price": start_price,
        "end_price": end_price,
        "max_price": max_price,
        "min_price": min_price,
        "change": change,
        "change_pct": change_pct,
    }


def analyze_stock_with_llm(symbol: str, df: pd.DataFrame, model_name: str = "qwen2.5") -> str:
    price_info = summarize_price(df)
    if not price_info:
        return "没有足够的价格数据，无法分析。"

    prompt = f"""你是一个专业的证券分析师，请用简洁的中文分析下面这只股票的近期走势。

股票代码：{symbol}

最近价格走势概况（取最后 30 条数据统计）：
- 起始收盘价：{price_info['start_price']:.2f}
- 最新收盘价：{price_info['end_price']:.2f}
- 涨跌幅：{price_info['change']:.2f}（{price_info['change_pct']:.2f}%）
- 最高价：{price_info['max_price']:.2f}
- 最低价：{price_info['min_price']:.2f}

请你回答：
1. 这只股票最近整体是上涨、下跌还是震荡？给出判断和简单理由。
2. 对普通投资者给出 3 条风险提示（不要给出具体买入/卖出建议）。

要求：
- 使用中文。
- 分点列出结论，结构清晰。"""

    try:
        from langchain_ollama import ChatOllama
    except Exception as e:
        return f"没有安装 langchain-ollama 或相关依赖，请先 pip install langchain langchain-ollama。错误：{e}"

    llm = ChatOllama(model=model_name, temperature=0.2)

    try:
        resp = llm.invoke(prompt)
    except Exception as e:
        return f"调用本地 Ollama 失败，请确认 ollama 正在运行且已 pull 模型 {model_name}。错误：{e}"

    content = getattr(resp, "content", None)
    if content is None:
        content = str(resp)
    return content
