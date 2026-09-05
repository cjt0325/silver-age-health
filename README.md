# 银龄健康通

面向老年人的 AI 健康教育与就医协同助手，适合安徽省 AI 大模型创新应用竞赛作品赛“智能交互/对话”方向演示。

## 项目能力

- 文字或中文语音输入健康问题
- 用通俗语言解释健康知识
- 生成就医准备清单
- 生成问诊问题清单
- 生成可复制给家属的提醒
- 朗读回答和大字号、高对比度界面
- 没有模型密钥时自动使用本地演示模式

项目不进行疾病诊断、不调整药物、不识别处方、不保存真实个人健康资料。

## 本地运行

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

打开 <http://127.0.0.1:5000>。如果 PowerShell 禁止激活脚本，也可以直接运行：

```powershell
.venv\Scripts\python.exe app.py
```

## 使用大模型服务（可选）

复制 `.env.example` 中的配置到当前终端环境。项目使用 OpenAI 兼容的 `/chat/completions` 接口，不配置 `OPENAI_API_KEY` 时不会影响演示。

```powershell
$env:OPENAI_API_KEY = "你的密钥"
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
$env:OPENAI_MODEL = "gpt-4o-mini"
.venv\Scripts\python.exe app.py
```

如果不想分开设置环境变量，可直接运行项目自带的安全启动脚本。脚本会在本机隐藏输入密钥，并在同一个进程内启动实时模型：

```powershell
.\start_live.ps1
```

启动后打开 <http://127.0.0.1:5000/api/config-status>，可以查看是否读到密钥、接口地址、模型名和最近一次失败原因；这里不会显示密钥。

## 推荐演示问题

1. 高血压平时要注意什么？
2. 感冒发热需要准备什么？
3. 我能不能把药停了？

第三个问题用于展示安全边界。浏览器支持语音识别时点击“开始说话”即可；不支持时直接文字输入，其他功能不受影响。

## 目录

- `app.py`：Flask 服务、知识检索、演示模式和大模型适配
- `data/health_knowledge.json`：演示知识库
- `templates/`、`static/`：老人友好网页
- `tests/`：自动化测试
- `submission/`：比赛作品报告、答辩材料和提交清单
- `docs/superpowers/specs/`、`docs/superpowers/plans/`：项目设计与实施记录

## 开源参考

提醒和记录交互思路参考 [Calendula](https://github.com/citiususc/calendula) 与 [Dosage](https://github.com/diegopvlk/Dosage)。本项目没有复制其代码；如后续复用代码，需先按对应 GPL-3.0 许可证履行开源义务。
