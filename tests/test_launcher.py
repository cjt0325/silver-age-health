from pathlib import Path


def test_launcher_uses_authorized_qwen_model():
    launcher = Path(__file__).resolve().parents[1] / "start_live.ps1"
    script = launcher.read_text(encoding="utf-8")
    assert "$env:OPENAI_MODEL = 'qwen3.8-flash'" in script


def test_env_example_has_safe_qwen_defaults_without_a_real_key():
    template = Path(__file__).resolve().parents[1] / ".env.example"
    content = template.read_text(encoding="utf-8")

    assert "OPENAI_API_KEY=your_dashscope_api_key_here" in content
    assert "https://dashscope.aliyuncs.com/compatible-mode/v1" in content
    assert "OPENAI_MODEL=qwen3.8-flash" in content
    assert "sk-" not in content
