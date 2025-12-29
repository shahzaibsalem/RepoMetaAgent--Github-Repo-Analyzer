import pytest
import yaml
from code.Agents.MetaDataAgent.nodes.MetaDataGenerator import load_prompt_section
from code.pathConfig import PROMPT_CONFIG_FILE

def get_all_agent_keys(yaml_path):
    """Extract all agent keys from the YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f)
    agents = full_config.get("tags_generation", {}).get("agents", {})
    return list(agents.keys())

@pytest.mark.parametrize("agent_key", get_all_agent_keys(PROMPT_CONFIG_FILE))
def test_load_prompt_section_real_yaml(agent_key):
    """Verify load_prompt_section loads every agent correctly from the actual YAML."""
    result = load_prompt_section(PROMPT_CONFIG_FILE, agent_key)

    # Required keys to validate
    expected_keys = ["llm", "role", "instruction", "output_constraints", "output_format", "goal"]
    for key in expected_keys:
        assert key in result, f"Missing key '{key}' in agent '{agent_key}'"
        assert result[key] is not None, f"Value for key '{key}' in agent '{agent_key}' is None"

    # Basic content checks
    assert isinstance(result["instruction"], str) and len(result["instruction"]) > 0
    assert isinstance(result["goal"], str) and len(result["goal"]) > 0
    assert len(result["output_constraints"]) > 0
    assert len(result["llm"]) > 0
    assert len(result["output_format"]) > 0
    assert len(result["role"]) > 0

