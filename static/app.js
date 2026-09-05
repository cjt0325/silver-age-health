const questionInput = document.querySelector('#question');
const askButton = document.querySelector('#ask-button');
const voiceButton = document.querySelector('#voice-button');
const voiceHint = document.querySelector('#voice-hint');
const speechStatus = document.querySelector('#speech-status');
const result = document.querySelector('#result');
let latestResponse = null;
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

function renderResponse(data) {
  latestResponse = data;
  document.querySelector('#answer').textContent = data.answer;
  document.querySelector('#when-to-seek-care').textContent = data.when_to_seek_care;
  document.querySelector('#family-message').textContent = data.family_message;
  document.querySelector('#safety-note').textContent = `安全提示：${data.safety_note}`;
  document.querySelector('#mode-note').textContent = data.mode === 'demo' ? '当前为本地演示模式，适合无网络答辩演示。' : '当前使用大模型服务生成内容。';
  setList('#attention', data.attention);
  setList('#visit-checklist', data.visit_checklist);
  setList('#doctor-questions', data.doctor_questions);
  result.hidden = false;
  result.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function askQuestion() {
  const question = questionInput.value.trim();
  if (!question) {
    questionInput.focus();
    voiceHint.textContent = '请先输入问题，或者点击“开始说话”。';
    return;
  }
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
  window.speechSynthesis.speak(new SpeechSynthesisUtterance(`${latestResponse.answer}。平时注意：${latestResponse.attention.join('；')}`));
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
setupVoice();
