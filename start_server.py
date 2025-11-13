#!/usr/bin/env python3
"""
智能理财炒股 Agent 启动脚本
"""

import os
import sys
import subprocess
import argparse
import signal
import time

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = [
        'flask', 'yfinance', 'pandas', 'numpy', 
        'ta', 'requests', 'pyyaml'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def check_config():
    """检查配置文件"""
    if not os.path.exists('config.yaml'):
        print("⚠️  配置文件 config.yaml 不存在，将使用默认配置")
        return True
    
    print("✅ 配置文件存在")
    return True

def start_server(host="0.0.0.0", port=12000, debug=False):
    """启动服务器"""
    print("🚀 启动智能理财炒股 Agent...")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print("📊 功能特性:")
    print("   • 多数据源股票数据获取")
    print("   • 专业技术指标分析")
    print("   • AI智能投资建议")
    print("   • 实时市场概览")
    print("   • 交互式图表展示")
    print()
    print("⚠️  投资有风险，决策需谨慎！")
    print("=" * 50)
    
    # 构建启动命令
    cmd = [sys.executable, 'app.py', '--host', host, '--port', str(port)]
    if not debug:
        cmd.append('--no-debug')
    
    try:
        # 启动服务器
        process = subprocess.Popen(cmd)
        
        # 等待用户中断
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 正在关闭服务器...")
            process.terminate()
            process.wait()
            print("✅ 服务器已关闭")
            
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='智能理财炒股 Agent 启动器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=12000, help='端口号 (默认: 12000)')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--check-only', action='store_true', help='仅检查环境，不启动服务器')
    
    args = parser.parse_args()
    
    print("🔍 检查运行环境...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查配置
    if not check_config():
        sys.exit(1)
    
    if args.check_only:
        print("✅ 环境检查完成，一切正常！")
        return
    
    # 启动服务器
    start_server(args.host, args.port, args.debug)

if __name__ == '__main__':
    main()