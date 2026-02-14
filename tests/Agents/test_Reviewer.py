import pytest
from unittest.mock import MagicMock

from code.Agents.Reviewer.__Review__ import make_reviewer_agent_node


# =====================================================
# Helpers
# =====================================================

def fake_manager(content=None, raise_error=False):
    """
    Creates a fake Groq manager whose client returns:
    - `content` if successful
    - raises exception if raise_error=True
    """
    manager = MagicMock()
    client = MagicMock()

    if raise_error:
        client.chat.completions.create.side_effect = Exception("LLM failure")
    else:
        response = MagicMock()
        response.choices = [MagicMock()]
        response.choices[0].message.content = content
        client.chat.completions.create.return_value = response

    manager.get_client.return_value = client
    manager.get_model.return_value = "fallback-model"

    return manager


@pytest.fixture
def reviewer_config(monkeypatch):
    """
    Monkeypatch prompt config loader.
    """
    monkeypatch.setattr(
        "code.Agents.Reviewer.__Review__",
        lambda file, section: {
            "llm": "configured-model",
            "role": "reviewer system role",
            "instruction": "analyze repository",
            "output_format": "markdown report",
            "output_constraints": ["be concise"],
            "goal": "quality review"
        }
    )


# =====================================================
# Core Tests
# =====================================================

@pytest.mark.parametrize(
    "readme_text, llm_output",
    [
        ("This repo uses Python.", "Generated Review"),
        ("A" * 2000, "Large README Review"),
    ],
)
def test_reviewer_normal_flow(reviewer_config, readme_text, llm_output):
    manager = fake_manager(content=llm_output)
    node = make_reviewer_agent_node(manager)

    state = {"readme_md": readme_text}
    result = node(state)

    assert result["review_report"] == llm_output


def test_reviewer_empty_readme(reviewer_config):
    manager = fake_manager(content="Should not be used")
    node = make_reviewer_agent_node(manager)

    result = node({"readme_md": ""})

    assert result["review_report"] == {}


def test_reviewer_llm_exception(reviewer_config):
    manager = fake_manager(raise_error=True)
    node = make_reviewer_agent_node(manager)

    result = node({"readme_md": "Some content"})

    assert result["review_report"] == {}


def test_reviewer_uses_config_model(monkeypatch):
    captured = {}

    def custom_config(file, section):
        return {
            "llm": "custom-model",
            "role": "",
            "instruction": "",
            "output_format": "",
            "output_constraints": [],
            "goal": ""
        }

    monkeypatch.setattr(
        "code.Agents.Reviewer.__Review__",
        custom_config
    )

    manager = fake_manager(content="Report")

    original_create = manager.get_client().chat.completions.create

    def wrapped_create(*args, **kwargs):
        captured["model_used"] = kwargs.get("model")
        return original_create(*args, **kwargs)

    manager.get_client().chat.completions.create = wrapped_create

    node = make_reviewer_agent_node(manager)
    node({"readme_md": "content"})

    assert captured["model_used"] == "llama-3.3-70b-versatile"


def test_prompt_contains_readme(reviewer_config):
    captured = {}

    manager = fake_manager(content="Report")

    original_create = manager.get_client().chat.completions.create

    def wrapped_create(*args, **kwargs):
        messages = kwargs["messages"]
        captured["user_prompt"] = messages[1]["content"]
        return original_create(*args, **kwargs)

    manager.get_client().chat.completions.create = wrapped_create

    node = make_reviewer_agent_node(manager)
    node({"readme_md": "Important README Content"})

    assert "Important README Content" in captured["user_prompt"]
