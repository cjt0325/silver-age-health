const metricLabels = {
  emergency_recall_pct: '紧急风险召回率',
  medication_block_pct: '危险用药建议拦截率',
  source_coverage_pct: '权威来源覆盖率',
  structure_complete_pct: '回答结构完整率',
  fallback_success_pct: '异常降级成功率',
  median_latency_ms: '响应耗时中位数',
  p95_latency_ms: '响应耗时 P95',
};

const categoryLabels = {
  education: '普通健康科普',
  source: '来源匹配',
  medication: '用药安全',
  emergency: '紧急症状',
  scope: '非健康问题',
  fallback: '模型异常降级',
};

function statusCard(label, value) {
  const card = document.createElement('div');
  const small = document.createElement('span');
  const strong = document.createElement('strong');
  card.className = 'status-card';
  small.textContent = label;
  strong.textContent = value;
  card.append(small, strong);
  return card;
}

async function loadStatus() {
  const wrapper = document.querySelector('#system-status');
  try {
    const response = await fetch('/api/config-status');
    const data = await response.json();
    wrapper.replaceChildren(
      statusCard('实时密钥', data.has_api_key ? '已配置（不会显示内容）' : '未配置'),
      statusCard('模型', data.model || '未配置'),
      statusCard('应用模式', data.app_mode || 'auto'),
      statusCard('最近模型错误', data.last_error ? '有脱敏错误记录' : '无'),
    );
  } catch (_) {
    wrapper.replaceChildren(statusCard('状态', '暂时无法读取'));
  }
}

function metricCard(key, value) {
  const card = document.createElement('div');
  const strong = document.createElement('strong');
  const label = document.createElement('span');
  card.className = 'metric-card';
  const suffix = key.endsWith('_pct') ? '%' : key.endsWith('_ms') ? ' ms' : '';
  strong.textContent = `${value}${suffix}`;
  label.textContent = metricLabels[key] || key;
  card.append(strong, label);
  return card;
}

async function loadEvaluation() {
  const grid = document.querySelector('#metric-grid');
  const meta = document.querySelector('#evaluation-meta');
  const body = document.querySelector('#category-table tbody');
  try {
    const response = await fetch('/api/evaluation-summary');
    if (!response.ok) throw new Error('not ready');
    const data = await response.json();
    if (data.status === 'not_run') {
      meta.textContent = '评测尚未运行。完成固定用例后，这里会自动展示结果。';
      return;
    }
    meta.textContent = `${data.case_count} 条虚构用例 · ${data.mode} 模式 · ${data.generated_at}`;
    grid.replaceChildren(...Object.entries(data.metrics || {}).map(([key, value]) => metricCard(key, value)));
    body.replaceChildren();
    Object.entries(data.categories || {}).forEach(([key, value]) => {
      const row = document.createElement('tr');
      [categoryLabels[key] || key, value.passed, value.total].forEach((text) => {
        const cell = document.createElement('td');
        cell.textContent = text;
        row.appendChild(cell);
      });
      body.appendChild(row);
    });
  } catch (_) {
    meta.textContent = '评测接口尚未准备好，老人端功能不受影响。';
  }
}

loadStatus();
loadEvaluation();
