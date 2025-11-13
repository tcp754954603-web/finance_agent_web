#!/usr/bin/env python3
"""
智能理财炒股 Agent 演示脚本
展示系统的主要功能
"""

import requests
import json
import time
from datetime import datetime

def demo_api_calls():
    """演示API调用"""
    base_url = "http://localhost:12000"
    
    print("🚀 智能理财炒股 Agent - 功能演示")
    print("=" * 50)
    
    # 1. 市场概览
    print("\n📊 1. 市场概览")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/api/market_overview")
        if response.status_code == 200:
            data = response.json()
            overview = data.get('market_overview', {})
            
            for name, info in overview.items():
                change_symbol = "+" if info['change_pct'] >= 0 else ""
                color = "🟢" if info['change_pct'] >= 0 else "🔴"
                print(f"{color} {name}: ${info['current_price']:.2f} ({change_symbol}{info['change_pct']:.2f}%)")
        else:
            print("❌ 市场概览获取失败")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 2. 股票分析演示
    demo_stocks = ["AAPL", "TSLA", "NVDA"]
    
    for i, symbol in enumerate(demo_stocks, 2):
        print(f"\n📈 {i}. {symbol} 股票分析")
        print("-" * 30)
        
        try:
            params = {
                'symbol': symbol,
                'period': '1mo',
                'interval': '1d',
                'analysis_type': 'quick'
            }
            
            response = requests.get(f"{base_url}/api/stock_data", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # 股票基本信息
                stock_info = data.get('stock_info', {})
                if stock_info and not stock_info.get('error'):
                    print(f"公司: {stock_info.get('name', 'N/A')}")
                    print(f"行业: {stock_info.get('sector', 'N/A')} - {stock_info.get('industry', 'N/A')}")
                    print(f"当前价格: ${stock_info.get('price', 0):.2f}")
                    print(f"市值: ${stock_info.get('market_cap', 0):,.0f}")
                
                # 技术分析
                technical = data.get('technical_indicators', {})
                if technical:
                    signals = technical.get('signals', {})
                    overall_signal = signals.get('overall_signal', 'neutral')
                    signal_strength = signals.get('signal_strength', 0)
                    
                    signal_emoji = "🟢" if overall_signal == "bullish" else "🔴" if overall_signal == "bearish" else "🟡"
                    print(f"交易信号: {signal_emoji} {overall_signal} (强度: {signal_strength:.2f})")
                
                # 数据点数量
                data_points = len(data.get('data', []))
                print(f"数据点: {data_points} 条记录")
                
            else:
                print(f"❌ {symbol} 数据获取失败")
                
        except Exception as e:
            print(f"❌ {symbol} 分析错误: {e}")
        
        # 添加延迟避免请求过快
        if i < len(demo_stocks) + 1:
            time.sleep(1)
    
    print("\n" + "=" * 50)
    print("✅ 演示完成！")
    print(f"🌐 访问 http://localhost:12000 查看完整界面")
    print("⚠️  投资有风险，决策需谨慎！")

def check_server():
    """检查服务器是否运行"""
    try:
        response = requests.get("http://localhost:12000/", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🔍 检查服务器状态...")
    
    if not check_server():
        print("❌ 服务器未运行！")
        print("请先启动服务器:")
        print("  python app.py")
        print("  或")
        print("  python start_server.py")
        return
    
    print("✅ 服务器运行正常")
    
    # 运行演示
    demo_api_calls()

if __name__ == '__main__':
    main()