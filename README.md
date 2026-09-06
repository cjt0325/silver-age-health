# 银龄健康通 2.0

面向老年人和家属的 AI 健康教育与可信就医导航助手。老人只需说一句话或输入一个问题，系统会给出通俗解释、红黄绿风险提示、就医准备清单、问诊问题、家属提醒和权威资料来源。

项目定位是健康教育与就医准备，不进行疾病诊断，不判断患病概率，不调整药物，不保存真实个人健康资料。

## 核心能力

- 老人大字号页面，支持中文语音输入和回答朗读。
- 红色“立即求助”、黄色“尽快咨询”、绿色“健康科普”三级安全路由。
- 从国家卫生健康委员会白名单资料中检索，并展示可点击来源。
- 千问 `qwen3.8-flash` 生成结构化通俗回答，安全规则在模型前后各检查一次。
- 可选问诊准备包，将开始时间、变化、用药和基础疾病整理成就医摘要。
- 家属提醒与家庭任务卡，一键复制后可自行发送。
- 模型不可用时自动返回本地安全内容，断网也能演示。
- 独立评委技术看板，展示运行状态和 30 条固定用例的可复现结果。

## 五分钟启动

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

打开 <http://127.0.0.1:5000>。未配置模型密钥时，系统自动使用本地演示模式。

## 使用千问实时模型

推荐使用安全启动脚本。脚本隐藏输入密钥，密钥只保留在当前进程中，不写入项目文件：

```powershell
.\start_live.ps1
```

默认配置：

- 接口：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- 模型：`qwen3.8-flash`
- 模式：`auto`

启动后访问 <http://127.0.0.1:5000/api/config-status> 可查看是否读取到密钥、模型名和脱敏错误；接口永远不会返回密钥内容。

## 推荐演示顺序

1. `老年人平时怎样预防跌倒？`：展示通俗回答和卫健委来源。
2. `降压药能不能停掉一半？`：展示黄色风险和用药决策拦截。
3. `老人突然胸痛而且呼吸困难怎么办？`：展示红色紧急规则直接处理，跳过大模型。
4. 点击“生成我的问诊准备包”：展示给医生的摘要和家庭任务。
5. 打开 <http://127.0.0.1:5000/evaluation>：展示技术证据。

## 运行固定评测

```powershell
.\.venv\Scripts\python.exe scripts\run_evaluation.py --mode demo
```

报告写入 `artifacts/evaluation_report.json`。当前本地安全基线共 30 条虚构用例，结果为 30/30 通过：紧急风险召回率、危险用药建议拦截率、权威来源覆盖率、回答结构完整率和异常降级成功率均为 100%。这些是工程与安全指标，不是临床准确率。

如需评估实时模型，可以在安全启动脚本创建的环境中运行：

```powershell
.\.venv\Scripts\python.exe scripts\run_evaluation.py --mode live
```

实时模式会产生多次模型调用，运行前应确认额度。

## 项目结构

- `app.py`：Flask 路由层。
- `health_core/safety.py`：三级风险和安全覆盖。
- `health_core/knowledge.py`：卫健委知识白名单和可解释检索。
- `health_core/model.py`：千问兼容接口与脱敏异常。
- `health_core/response.py`：提示词、结构化回答和降级。
- `health_core/visit_pack.py`：无存储问诊准备包。
- `health_core/evaluation.py`：固定用例与指标计算。
- `templates/`、`static/`：老人端与评委技术看板。
- `data/`：六类健康知识和 30 条虚构评测用例。
- `submission/`：盲审报告、答辩大纲、演示脚本和提交清单。

## 权威资料与开源参考

健康内容来源于国家卫生健康委员会公开资料：

- [老年健康核心信息](https://www.nhc.gov.cn/jtfzs/s7882t/201410/dcc9139b960f4828a2c705a4f070da72.shtml)
- [老年失能预防核心信息](https://www.nhc.gov.cn/lljks/c100158/201908/434ad204c8cd4972bb4c9eb42f748f43.shtml)
- [关于全面加强老年健康服务工作的通知](https://www.nhc.gov.cn/lljks/c100158/202201/96f260cf07684d90840484de01ca97da.shtml)

提醒和记录交互思路参考 [Calendula](https://github.com/citiususc/calendula) 与 [Dosage](https://github.com/diegopvlk/Dosage)。本项目未复制其源代码；如后续直接复用代码，需遵守相应 GPL-3.0 许可证。
