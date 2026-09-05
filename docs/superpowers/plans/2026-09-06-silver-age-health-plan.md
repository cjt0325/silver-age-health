# 银龄健康通 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a one-week, demo-ready elderly health education and medical-visit coordination web application for the Anhui AI large-model competition.

**Architecture:** A Flask server serves a large-text elderly-friendly page and a JSON API. The API performs input validation, safety checks, lightweight knowledge retrieval, and either calls an OpenAI-compatible chat endpoint or returns a deterministic demo response. The browser supplies Chinese speech recognition and text-to-speech when supported.

**Tech Stack:** Python 3.10+, Flask, pytest, native browser Web Speech APIs, JSON knowledge data, urllib from the Python standard library for model calls.

## Global Constraints

- No diagnosis, medication changes, prescription recognition, or real personal health-data storage.
- The project must run without an API key in demo mode.
- The blind-review materials must not contain school, team, advisor, or person names.
- The interface must support large text, high contrast, clear actions, and a text-input fallback when speech is unavailable.
- Keep dependencies to Flask and pytest; use the standard library for HTTP and JSON handling.

## File Map

- Create: `app.py` — Flask routes, validation, safety guard, model adapter, and response shaping.
- Create: `data/health_knowledge.json` — small curated knowledge base for demo topics.
- Create: `templates/index.html` — accessible elderly-facing page.
- Create: `static/style.css` — large-text, high-contrast responsive styling.
- Create: `static/app.js` — ask flow, speech recognition, speech synthesis, copying, and rendering.
- Create: `tests/test_core.py` — behavior tests for validation, safety, fallback output, and response shape.
- Create: `requirements.txt` and `.env.example` — installation and configuration.
- Create: `README.md` — five-minute startup and demo instructions.
- Create: `submission/作品报告_盲审版.md` — <=10-page-equivalent report content without identity fields.
- Create: `submission/答辩PPT大纲.md` — slide-by-slide presentation content.
- Create: `submission/项目演示脚本.md` — a three-minute live demo script.
- Create: `submission/技术说明.md` — architecture, safety, deployment, and open-source references.
- Create: `submission/材料提交清单.md` — final packaging checklist.

### Task 1: Define tested core behavior

**Files:**
- Create: `tests/test_core.py`

**Interfaces:**
- The tests will import `validate_question`, `is_high_risk_question`, `build_demo_response`, and `prepare_response` from `app.py`.

- [ ] **Step 1: Write failing tests**

```python
from app import build_demo_response, is_high_risk_question, prepare_response, validate_question


def test_blank_question_is_rejected():
    assert validate_question("   ") == "请先输入或说出一个健康问题。"


def test_high_risk_question_is_detected():
    assert is_high_risk_question("我能不能把药停了？") is True


def test_demo_response_contains_three_lists():
    result = build_demo_response("高血压平时要注意什么？")
    assert result["answer"]
    assert result["visit_checklist"]
    assert result["doctor_questions"]
    assert result["family_message"]


def test_prepare_response_keeps_required_shape():
    result = prepare_response("感冒发热要注意什么？", mode="demo")
    assert set(result) >= {
        "answer", "attention", "when_to_seek_care", "visit_checklist",
        "doctor_questions", "family_message", "safety_note", "mode"
    }
```

- [ ] **Step 2: Run the focused tests and verify the expected import failure**

Run: `python -m pytest tests/test_core.py -q`

Expected: FAIL because `app.py` and the requested functions do not yet exist.

### Task 2: Implement the tested core and model fallback

**Files:**
- Create: `app.py`
- Create: `data/health_knowledge.json`
- Modify: `tests/test_core.py` only if an assertion needs to match the agreed response contract.

**Interfaces:**
- `validate_question(question: str) -> str | None`
- `is_high_risk_question(question: str) -> bool`
- `build_demo_response(question: str) -> dict`
- `prepare_response(question: str, mode: str | None = None) -> dict`

- [ ] **Step 1: Implement the minimum functions and Flask endpoint**

`app.py` must validate a trimmed question, detect the terms `诊断`, `改药`, `停药`, `药量`, `急救`, and `能不能不去医院`, load JSON knowledge, provide a deterministic response for demo mode, and expose `POST /api/ask` with `{ "question": "..." }` input. A configured `OPENAI_API_KEY` uses the OpenAI-compatible endpoint; any exception falls back to the deterministic response.

- [ ] **Step 2: Run the focused tests**

Run: `python -m pytest tests/test_core.py -q`

Expected: all focused tests pass.

- [ ] **Step 3: Run the Flask test client smoke check**

Run: `python -c "from app import app; c=app.test_client(); r=c.post('/api/ask', json={'question':'高血压平时要注意什么？'}); print(r.status_code, sorted(r.json.keys()))"`

Expected: status `200` and the required response keys.

### Task 3: Add the elderly-friendly browser interface

**Files:**
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `static/app.js`

**Interfaces:**
- The page posts question text to `/api/ask`.
- The page renders the JSON fields `answer`, `attention`, `when_to_seek_care`, `visit_checklist`, `doctor_questions`, `family_message`, `safety_note`, and `mode`.

- [ ] **Step 1: Add the page with keyboard-accessible controls**

Include one large question input, “开始说话”, “提交问题”, “朗读回答”, “复制家属提醒”, a visible speech-support status, example questions, and an always-visible safety note.

- [ ] **Step 2: Add styling**

Use a minimum 20px base font, strong color contrast, large buttons, a single-column layout below 800px, and visible focus outlines. Do not require drag, hover, or precise small clicks.

- [ ] **Step 3: Add browser behavior**

Use `SpeechRecognition` or `webkitSpeechRecognition` with `zh-CN`; if unavailable, show a text fallback. Use `speechSynthesis` for reading the answer when available. Copy only the generated family reminder.

- [ ] **Step 4: Start the server and perform a manual browser smoke check**

Run: `python app.py`

Check: open `http://127.0.0.1:5000`, submit the example question, confirm the answer and all three generated materials appear, and confirm the unsupported-speech message does not block text input.

### Task 4: Add setup and competition deliverables

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `README.md`
- Create: `submission/作品报告_盲审版.md`
- Create: `submission/答辩PPT大纲.md`
- Create: `submission/项目演示脚本.md`
- Create: `submission/技术说明.md`
- Create: `submission/材料提交清单.md`

**Interfaces:**
- README commands must match the actual files: `python -m venv .venv`, install requirements, and `python app.py`.
- Submission documents must describe the same feature set and safety boundaries as `app.py`.

- [ ] **Step 1: Write the startup instructions and environment example**

Document demo mode, OpenAI-compatible configuration, browser speech limitations, and the sample questions.

- [ ] **Step 2: Write the blind-review work report**

Include problem statement, user research assumptions, solution, large-model use, technical route, innovation, social value, safety, testing, limitations, and future work. Do not include identity placeholders or personal names.

- [ ] **Step 3: Write the presentation outline and demo script**

Cover the elderly scenario, live question, generated visit checklist, doctor questions, family reminder, safety boundary, and one-week feasibility.

- [ ] **Step 4: Write technical notes and submission checklist**

List open-source references as inspiration only, licenses to respect, local run steps, screenshots to capture, and the files to package.

### Task 5: Full verification

**Files:**
- Verify all created files.

- [ ] **Step 1: Run all automated tests**

Run: `python -m pytest -q`

Expected: zero failures.

- [ ] **Step 2: Compile the Python file**

Run: `python -m py_compile app.py`

Expected: exit code `0`.

- [ ] **Step 3: Validate document consistency**

Run: `rg -n "诊断|改药|停药|药量|盲审|家属提醒|问诊问题" app.py README.md submission docs`

Expected: safety boundaries and named deliverables appear in both code/docs, with no school/team/person identity.

- [ ] **Step 4: Inspect the final file tree and run the HTTP smoke check**

Run: `python -c "from app import app; c=app.test_client(); r=c.post('/api/ask', json={'question':'我能不能把药停了？'}); print(r.status_code, r.json['safety_note'])"`

Expected: `200` and a non-empty safety note.
