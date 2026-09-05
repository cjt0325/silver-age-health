from pathlib import Path


def test_launcher_uses_authorized_qwen_model():
    launcher = Path(__file__).resolve().parents[1] / "start_live.ps1"
    script = launcher.read_text(encoding="utf-8")
    assert "$env:OPENAI_MODEL = 'qwen3.8-flash'" in script
