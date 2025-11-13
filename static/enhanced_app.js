// 全局变量
let priceChart = null;
let indicatorChart = null;
let currentIndicator = 'rsi';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
  loadMarketOverview();
});

function initializeApp() {
  const form = document.getElementById('queryForm');
  const input = document.getElementById('symbolInput');
  
  // 表单提交事件
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const symbol = input.value.trim();
    if (!symbol) return;
    
    const period = document.getElementById('periodSelect').value;
    const interval = document.getElementById('intervalSelect').value;
    const analysisType = document.getElementById('analysisSelect').value;
    
    fetchStockData(symbol, period, interval, analysisType);
  });
  
  // 技术指标标签页切换
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentIndicator = btn.dataset.indicator;
      // 重新渲染指标图表
      if (window.currentStockData) {
        renderIndicatorChart(window.currentStockData);
      }
    });
  });
  
  // 如果有默认股票代码，自动查询
  if (input.value) {
    fetchStockData(input.value.trim(), '1mo', '1d', 'quick');
  }
}

async function loadMarketOverview() {
  const indicesGrid = document.getElementById('indicesGrid');
  
  try {
    indicesGrid.innerHTML = '<div class="loading">加载市场数据中...</div>';
    
    const response = await fetch('/api/market_overview');
    const data = await response.json();
    
    if (!response.ok || data.error) {
      indicesGrid.innerHTML = '<div class="loading">市场数据加载失败</div>';
      return;
    }
    
    const overview = data.market_overview;
    let html = '';
    
    for (const [name, info] of Object.entries(overview)) {
      const changeClass = info.change_pct >= 0 ? 'positive' : 'negative';
      const changeSymbol = info.change_pct >= 0 ? '+' : '';
      
      html += `
        <div class="index-card">
          <div class="index-name">${name}</div>
          <div class="index-price">$${info.current_price.toFixed(2)}</div>
          <div class="index-change ${changeClass}">
            ${changeSymbol}${info.change.toFixed(2)} (${changeSymbol}${info.change_pct.toFixed(2)}%)
          </div>
        </div>
      `;
    }
    
    indicesGrid.innerHTML = html;
    
  } catch (error) {
    console.error('加载市场概览失败:', error);
    indicesGrid.innerHTML = '<div class="loading">市场数据加载失败</div>';
  }
}

async function fetchStockData(symbol, period, interval, analysisType) {
  const statusEl = document.getElementById('status');
  const stockInfoBox = document.getElementById('stockInfoBox');
  const technicalSummary = document.getElementById('technicalSummary');
  const tradingSignals = document.getElementById('tradingSignals');
  const analysisBox = document.getElementById('analysisBox');
  
  // 显示加载状态
  statusEl.className = 'status loading';
  statusEl.textContent = `正在分析 ${symbol}...`;
  
  stockInfoBox.innerHTML = '<div class="loading">加载股票信息中...</div>';
  technicalSummary.innerHTML = '<div class="loading">计算技术指标中...</div>';
  tradingSignals.innerHTML = '<div class="loading">生成交易信号中...</div>';
  analysisBox.innerHTML = '<div class="loading">AI分析中...</div>';
  
  try {
    const params = new URLSearchParams({
      symbol: symbol,
      period: period,
      interval: interval,
      analysis_type: analysisType
    });
    
    const response = await fetch(`/api/stock_data?${params}`);
    const data = await response.json();
    
    if (!response.ok || data.error) {
      const errorMsg = data.error || `HTTP错误: ${response.status}`;
      statusEl.className = 'status error';
      statusEl.textContent = `❌ 错误: ${errorMsg}`;
      
      stockInfoBox.innerHTML = '<div class="loading">数据加载失败</div>';
      technicalSummary.innerHTML = '<div class="loading">技术分析失败</div>';
      tradingSignals.innerHTML = '<div class="loading">信号生成失败</div>';
      analysisBox.innerHTML = '<div class="loading">AI分析失败</div>';
      return;
    }
    
    // 保存数据供其他函数使用
    window.currentStockData = data;
    
    // 更新状态
    statusEl.className = 'status success';
    statusEl.textContent = `✅ 成功获取 ${symbol} 数据 (${data.data.length} 条记录)`;
    
    // 更新各个面板
    updateStockInfo(data.stock_info);
    updateTechnicalSummary(data.technical_indicators.summary);
    updateTradingSignals(data.technical_indicators.signals);
    updateAnalysis(data.analysis);
    
    // 渲染图表
    renderPriceChart(data);
    renderIndicatorChart(data);
    
  } catch (error) {
    console.error('获取股票数据失败:', error);
    statusEl.className = 'status error';
    statusEl.textContent = `❌ 请求异常: ${error.message}`;
  }
}

function updateStockInfo(stockInfo) {
  const stockInfoBox = document.getElementById('stockInfoBox');
  
  if (!stockInfo || stockInfo.error) {
    stockInfoBox.innerHTML = '<div class="loading">股票信息不可用</div>';
    return;
  }
  
  const formatValue = (value, suffix = '') => {
    if (value === null || value === undefined || value === 0) return 'N/A';
    if (typeof value === 'number') {
      return value.toLocaleString() + suffix;
    }
    return value;
  };
  
  const formatMarketCap = (value) => {
    if (!value || value === 0) return 'N/A';
    if (value > 1e12) return `$${(value/1e12).toFixed(2)}T`;
    if (value > 1e9) return `$${(value/1e9).toFixed(2)}B`;
    if (value > 1e6) return `$${(value/1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
  };
  
  const html = `
    <div class="info-item">
      <span class="info-label">公司名称:</span>
      <span class="info-value">${stockInfo.name || 'N/A'}</span>
    </div>
    <div class="info-item">
      <span class="info-label">行业:</span>
      <span class="info-value">${stockInfo.sector || 'N/A'}</span>
    </div>
    <div class="info-item">
      <span class="info-label">市值:</span>
      <span class="info-value">${formatMarketCap(stockInfo.market_cap)}</span>
    </div>
    <div class="info-item">
      <span class="info-label">市盈率:</span>
      <span class="info-value">${formatValue(stockInfo.pe_ratio)}</span>
    </div>
    <div class="info-item">
      <span class="info-label">股息率:</span>
      <span class="info-value">${formatValue(stockInfo.dividend_yield * 100, '%')}</span>
    </div>
    <div class="info-item">
      <span class="info-label">Beta系数:</span>
      <span class="info-value">${formatValue(stockInfo.beta)}</span>
    </div>
    <div class="info-item">
      <span class="info-label">当前价格:</span>
      <span class="info-value">$${formatValue(stockInfo.price)}</span>
    </div>
    <div class="info-item">
      <span class="info-label">交易所:</span>
      <span class="info-value">${stockInfo.exchange || 'N/A'}</span>
    </div>
  `;
  
  stockInfoBox.innerHTML = html;
}

function updateTechnicalSummary(summary) {
  const technicalSummary = document.getElementById('technicalSummary');
  technicalSummary.innerHTML = `<pre>${summary || '暂无技术分析数据'}</pre>`;
}

function updateTradingSignals(signals) {
  const tradingSignals = document.getElementById('tradingSignals');
  
  if (!signals || !signals.signals) {
    tradingSignals.innerHTML = '<div class="loading">暂无交易信号</div>';
    return;
  }
  
  const getSignalClass = (signal) => {
    if (signal === 'bullish') return 'signal-bullish';
    if (signal === 'bearish') return 'signal-bearish';
    return 'signal-neutral';
  };
  
  const getSignalIcon = (signal) => {
    if (signal === 'bullish') return '↗';
    if (signal === 'bearish') return '↘';
    return '→';
  };
  
  let html = `
    <div class="signal-item">
      <div class="signal-icon ${getSignalClass(signals.overall_signal)}">
        ${getSignalIcon(signals.overall_signal)}
      </div>
      <div>
        <strong>总体信号: ${signals.overall_signal}</strong>
        <br>
        <small>信号强度: ${(signals.signal_strength * 100).toFixed(1)}%</small>
      </div>
    </div>
  `;
  
  if (signals.signals && signals.signals.length > 0) {
    signals.signals.forEach(signal => {
      html += `
        <div class="signal-item">
          <div class="signal-icon signal-neutral">•</div>
          <div>${signal}</div>
        </div>
      `;
    });
  }
  
  tradingSignals.innerHTML = html;
}

function updateAnalysis(analysis) {
  const analysisBox = document.getElementById('analysisBox');
  analysisBox.innerHTML = `<pre>${analysis || '暂无分析数据'}</pre>`;
}

function renderPriceChart(data) {
  const ctx = document.getElementById('priceChart').getContext('2d');
  
  if (priceChart) {
    priceChart.destroy();
  }
  
  const labels = data.data.map(item => item.date);
  const prices = data.data.map(item => item.close);
  const volumes = data.data.map(item => item.volume);
  
  priceChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: `${data.symbol} 收盘价`,
        data: prices,
        borderColor: '#2a5298',
        backgroundColor: 'rgba(42, 82, 152, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: `${data.symbol} 价格走势 (${data.period})`
        },
        legend: {
          display: true
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: '时间'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: '价格 ($)'
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  });
}

function renderIndicatorChart(data) {
  const ctx = document.getElementById('indicatorChart').getContext('2d');
  
  if (indicatorChart) {
    indicatorChart.destroy();
  }
  
  const labels = data.data.map(item => item.date);
  let datasets = [];
  let title = '';
  let yAxisTitle = '';
  
  switch (currentIndicator) {
    case 'rsi':
      if (data.rsi && data.rsi.length > 0) {
        datasets = [{
          label: 'RSI',
          data: data.rsi.map(item => item.value),
          borderColor: '#ff6b6b',
          backgroundColor: 'rgba(255, 107, 107, 0.1)',
          borderWidth: 2,
          fill: false
        }];
        title = 'RSI 相对强弱指数';
        yAxisTitle = 'RSI';
      }
      break;
      
    case 'macd':
      // MACD数据需要从技术指标中获取
      datasets = [{
        label: 'MACD',
        data: data.data.map(() => Math.random() * 2 - 1), // 临时数据
        borderColor: '#4ecdc4',
        backgroundColor: 'rgba(78, 205, 196, 0.1)',
        borderWidth: 2,
        fill: false
      }];
      title = 'MACD 指标';
      yAxisTitle = 'MACD';
      break;
      
    case 'volume':
      datasets = [{
        label: '成交量',
        data: data.data.map(item => item.volume),
        borderColor: '#45b7d1',
        backgroundColor: 'rgba(69, 183, 209, 0.3)',
        borderWidth: 1,
        fill: true
      }];
      title = '成交量';
      yAxisTitle = '成交量';
      break;
  }
  
  indicatorChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: title
        },
        legend: {
          display: true
        }
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: '时间'
          }
        },
        y: {
          display: true,
          title: {
            display: true,
            text: yAxisTitle
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index'
      }
    }
  });
}