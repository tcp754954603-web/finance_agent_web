let chart = null;

async function fetchStock(symbol) {
  const statusEl = document.getElementById('status');
  const summaryBox = document.getElementById('summaryBox');
  const analysisBox = document.getElementById('analysisBox');

  statusEl.textContent = `正在查询 ${symbol}...`;
  summaryBox.textContent = '加载中...';
  analysisBox.textContent = '加载中...';

  try {
    const resp = await fetch(`/api/stock?symbol=${encodeURIComponent(symbol)}`);
    const data = await resp.json();

    if (!resp.ok || data.error) {
      const msg = data.error || `HTTP 错误: ${resp.status}`;
      statusEl.textContent = `❌ 出错：${msg}`;
      summaryBox.textContent = '暂无数据';
      analysisBox.textContent = '暂无分析';
      return;
    }

    statusEl.textContent = `✅ 已获取 ${symbol} 数据，共 ${data.points.length} 条记录`;

    const s = data.summary;
    const lines = [
      `股票代码：${s.symbol}`,
      `时间范围：${s.first_time}  ~  ${s.last_time}`,
      `起始收盘价：${s.first_close.toFixed(2)}`,
      `最新收盘价：${s.last_close.toFixed(2)}`,
      `涨跌：${s.change.toFixed(2)}  (${s.change_pct.toFixed(2)}%)`,
      `最高价：${s.high.toFixed(2)}`,
      `最低价：${s.low.toFixed(2)}`,
    ];
    summaryBox.textContent = lines.join('\n');

    const labels = data.points.map(p => p.time);
    const closes = data.points.map(p => p.close);
    renderChart(labels, closes, s.symbol);

    if (data.llm_analysis) {
      analysisBox.textContent = data.llm_analysis;
    } else {
      analysisBox.textContent = '未启用 LLM 分析或调用失败。可以在 config.yaml 中开启 llm.enable。';
    }

  } catch (err) {
    statusEl.textContent = `❌ 请求异常：${err}`;
    summaryBox.textContent = '暂无数据';
    analysisBox.textContent = '暂无分析';
  }
}

function renderChart(labels, data, symbol) {
  const ctx = document.getElementById('priceChart').getContext('2d');
  if (chart) {
    chart.destroy();
  }
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: `${symbol} 收盘价`,
        data: data,
        fill: false,
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          display: false
        }
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('queryForm');
  const input = document.getElementById('symbolInput');

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const symbol = input.value.trim();
    if (!symbol) return;
    fetchStock(symbol);
  });

  if (input.value) {
    fetchStock(input.value.trim());
  }
});
