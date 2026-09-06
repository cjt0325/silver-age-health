from pathlib import Path


def test_qwen_startup_assets_use_safe_authorized_defaults():
    launcher = Path(__file__).resolve().parents[1] / "start_live.ps1"
    script = launcher.read_text(encoding="utf-8")
    assert "$env:OPENAI_MODEL = 'qwen3.8-flash'" in script

    template = Path(__file__).resolve().parents[1] / ".env.example"
    content = template.read_text(encoding="utf-8")

    assert "OPENAI_API_KEY=your_dashscope_api_key_here" in content
    assert "https://dashscope.aliyuncs.com/compatible-mode/v1" in content
    assert "OPENAI_MODEL=qwen3.8-flash" in content
    assert "sk-" not in content
