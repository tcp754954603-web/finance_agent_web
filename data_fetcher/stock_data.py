import requests
import pandas as pd


def get_stock_data(symbol: str, api_key: str, base_url: str = "https://www.alphavantage.co/query"):
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",
        "apikey": api_key,
    }

    try:
        resp = requests.get(base_url, params=params, timeout=15)
    except Exception as e:
        print(f"❌ [{symbol}] 请求异常: {e}")
        return None

    print(f"[DEBUG] 请求 URL: {resp.url}")
    if resp.status_code != 200:
        print(f"❌ [{symbol}] HTTP 状态码异常: {resp.status_code}")
        return None

    data = resp.json()
    top_keys = list(data.keys())
    print(f"[DEBUG] 顶层字段: {top_keys}")

    key = "Time Series (5min)"
    if key not in data:
        print(f"⚠️ [{symbol}] 返回中没有 {key}，可能是频率限制或代码错误: {data}")
        return None

    ts = data[key]
    df = pd.DataFrame.from_dict(ts, orient="index")
    df.columns = ["Open", "High", "Low", "Close", "Volume"]
    df.index = pd.to_datetime(df.index)

    for col in ["Open", "High", "Low", "Close", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.sort_index()
    return df
