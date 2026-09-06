const questionInput = document.querySelector('#question');
const askButton = document.querySelector('#ask-button');
const voiceButton = document.querySelector('#voice-button');
const voiceHint = document.querySelector('#voice-hint');
const speechStatus = document.querySelector('#speech-status');
const result = document.querySelector('#result');
const visitPackButton = document.querySelector('#visit-pack-button');
const visitPackForm = document.querySelector('#visit-pack-form');
let latestResponse = null;
let latestQuestion = '';
let recognition = null;

function setList(selector, values) {
  const list = document.querySelector(selector);
  list.replaceChildren();
  (values || []).forEach((value) => {
    const item = document.createElement('li');
    item.textContent = value;
    list.appendChild(item);
  });
}

function renderRisk(risk) {
  const banner = document.querySelector('#risk-banner');
  const level = ['red', 'yellow', 'green'].includes(risk?.level) ? risk.level : 'green';
  banner.className = `risk-banner risk-${level}`;
  banner.querySelector('.risk-icon').textContent = level === 'red' ? '!' : level === 'yellow' ? '△' : '✓';
  document.querySelector('#risk-label').textContent = risk?.label || '健康科普';
  document.querySelector('#risk-action').textContent = risk?.action || '请结合自身情况咨询专业人员。';
}

function renderSources(sources) {
  const list = document.querySelector('#source-list');
  const empty = document.querySelector('#source-empty');
  list.replaceChildren();
  (sources || []).forEach((source) => {
    try {
      const url = new URL(source.url);
      if (url.protocol !== 'https:' || url.hostname !== 'www.nhc.gov.cn') return;
      const item = document.createElement('li');
      const link = document.createElement('a');
      const meta = document.createElement('span');
      link.href = url.href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = source.title;
      meta.className = 'source-meta';
      meta.textContent = `${source.organization} · 发布于 ${source.published_at}`;
      item.append(link, meta);
      list.appendChild(item);
    } catch (_) {
      // Invalid or non-whitelisted URLs are deliberately omitted.
    }
  });
  empty.hidden = list.children.length > 0;
}

function renderTrace(trace) {
  const wrapper = document.querySelector('#trace-summary');
  wrapper.replaceChildren();
  const values = [
    `模式：${trace?.mode || '未知'}`,
    `模型：${trace?.model || '本地安全规则'}`,
    `耗时：${trace?.elapsed_ms ?? 0} 毫秒`,
    `知识命中：${trace?.knowledge_hits ?? 0} 条`,
  ];
  values.forEach((value) => {
    const span = document.createElement('span');
    span.textContent = value;
    wrapper.appendChild(span);
  });
}

function renderResponse(data) {
  latestResponse = data;
  renderRisk(data.risk);
  document.querySelector('#answer').textContent = data.answer;
  document.querySelector('#when-to-seek-care').textContent = data.when_to_seek_care;
  document.querySelector('#family-message').textContent = data.family_message;
  document.querySelector('#safety-note').textContent = `安全提示：${data.safety_note}`;
  const modeMessages = {
    demo: '当前使用本地安全内容，适合无网络答辩演示。',
    live: '当前使用千问大模型，并经过本地安全规则复核。',
    safety: '当前由本地紧急安全规则直接处理，未调用大模型。',
    scope: '当前问题不在服务范围内，系统未调用大模型。',
  };
  document.querySelector('#mode-note').textContent = modeMessages[data.mode] || '当前响应模式未知。';
  setList('#attention', data.attention);
  setList('#visit-checklist', data.visit_checklist);
  setList('#doctor-questions', data.doctor_questions);
  renderSources(data.sources);
  renderTrace(data.trace);
  document.querySelector('#visit-pack-panel').hidden = !data.follow_up_available;
  visitPackForm.hidden = true;
  visitPackButton.setAttribute('aria-expanded', 'false');
  document.querySelector('#visit-pack-result').hidden = true;
  result.hidden = false;
  if (data.risk?.level === 'red' && window.speechSynthesis) window.speechSynthesis.cancel();
  result.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function askQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    questionInput.focus();
    voiceHint.textContent = '请先输入问题，或者点击“开始说话”。';
    return;
  }
  latestQuestion = question;
  askButton.disabled = true;
  askButton.textContent = '正在整理…';
  try {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '暂时无法回答');
    renderResponse(data);
  } catch (error) {
    voiceHint.textContent = error.message || '暂时无法连接，请稍后再试。';
  } finally {
    askButton.disabled = false;
    askButton.textContent = '✨ 帮我讲明白';
  }
}

function setupVoice() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    speechStatus.textContent = '请使用文字输入';
    voiceHint.textContent = '当前浏览器不支持语音识别，直接打字也可以使用全部功能。';
    voiceButton.disabled = true;
    return;
  }
  recognition = new SpeechRecognition();
  recognition.lang = 'zh-CN';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  speechStatus.textContent = '语音功能可用';
  speechStatus.classList.add('ready');
  recognition.onstart = () => {
    speechStatus.textContent = '正在听，请说话';
    speechStatus.classList.add('listening');
    voiceButton.textContent = '⏹ 停止说话';
  };
  recognition.onresult = (event) => {
    questionInput.value = event.results[0][0].transcript;
    voiceHint.textContent = '已经听到了，确认内容后点击“帮我讲明白”。';
  };
  recognition.onerror = () => {
    voiceHint.textContent = '没有听清楚，请再试一次，或直接输入问题。';
  };
  recognition.onend = () => {
    speechStatus.textContent = '语音功能可用';
    speechStatus.classList.remove('listening');
    voiceButton.textContent = '🎙 开始说话';
  };
}

voiceButton.addEventListener('click', () => {
  if (!recognition) return;
  if (speechStatus.classList.contains('listening')) recognition.stop();
  else recognition.start();
});
askButton.addEventListener('click', askQuestion);
questionInput.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') askQuestion();
});
document.querySelectorAll('[data-question]').forEach((button) => {
  button.addEventListener('click', () => {
    questionInput.value = button.dataset.question;
    questionInput.focus();
  });
});
document.querySelector('#read-button').addEventListener('click', () => {
  if (!latestResponse || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const speech = `${latestResponse.risk.action}。${latestResponse.answer}。平时注意：${latestResponse.attention.join('；')}`;
  const utterance = new SpeechSynthesisUtterance(speech);
  utterance.lang = 'zh-CN';
  window.speechSynthesis.speak(utterance);
});
document.querySelector('#copy-button').addEventListener('click', async () => {
  if (!latestResponse) return;
  try {
    await navigator.clipboard.writeText(latestResponse.family_message);
    document.querySelector('#copy-status').textContent = '提醒已复制，可以粘贴发给家人。';
  } catch (_) {
    document.querySelector('#copy-status').textContent = '复制失败，请手动选中上面的提醒文字。';
  }
});
visitPackButton.addEventListener('click', () => {
  const willOpen = visitPackForm.hidden;
  visitPackForm.hidden = !willOpen;
  visitPackButton.setAttribute('aria-expanded', String(willOpen));
  if (willOpen) document.querySelector('#detail-started').focus();
});
visitPackForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const submitButton = visitPackForm.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  try {
    const details = {
      started: document.querySelector('#detail-started').value,
      change: document.querySelector('#detail-change').value,
      medications: document.querySelector('#detail-medications').value,
      conditions: document.querySelector('#detail-conditions').value,
    };
    const response = await fetch('/api/visit-pack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: latestQuestion, details }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || '准备包生成失败');
    document.querySelector('#pack-summary').textContent = data.summary;
    setList('#pack-materials', data.materials);
    setList('#pack-questions', data.doctor_questions);
    setList('#pack-family-tasks', data.family_tasks);
    document.querySelector('#pack-privacy-note').textContent = data.privacy_note;
    document.querySelector('#visit-pack-result').hidden = false;
  } catch (error) {
    voiceHint.textContent = error.message || '准备包生成失败，请稍后重试。';
  } finally {
    submitButton.disabled = false;
  }
});

setupVoice();
