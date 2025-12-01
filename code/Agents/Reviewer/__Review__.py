import yaml
import os
from typing import Dict, Any, Callable, List
from pathConfig import PROMPT_CONFIG_FILE



def load_prompt_section(
    file_path: str,
    agent_key: str
) -> Dict[str, Any]:
    """
    Universal loader for any prompt section in tags_generation.agents.

    Args:
        file_path: Path to YAML config
        agent_key: Name of the agent section, e.g.:
            - "short_summary_generator"
            - "long_summary_generator"
            - "metadata_recommendation_generator"

    Returns:
        A dictionary with:
            llm, role, instruction,
            output_constraints, output_format, goal
    """

    if not os.path.exists(file_path):
        print(f"!!! ERROR: YAML file not found at: {file_path}")
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            full_config = yaml.safe_load(f)
        agents = full_config.get("tags_generation", {}).get("agents", {})
        section = agents.get(agent_key, {})

        prompt_config = section.get("prompt_config", {})

        return {
            "llm": section.get("llm"),
            "role": prompt_config.get("role"),
            "instruction": prompt_config.get("instruction"),
            "output_constraints": prompt_config.get("output_constraints", []),
            "output_format": prompt_config.get("output_format"),
            "goal": prompt_config.get("goal"),
        }

    except Exception as e:
        print(f"!!! ERROR: Failed to load agent '{agent_key}': {e}")
        return {}



def make_reviewer_agent_node(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    client = groq_manager_instance.get_client()
    model = groq_manager_instance.get_model()

    config = load_prompt_section(PROMPT_CONFIG_FILE, "reviewer_agent")

    llm_model = config.get("llm") or model
    system_role = config.get("role", "")
    instruction = config.get("instruction", "")
    output_format = config.get("output_format", "")
    output_constraints = config.get("output_constraints", [])
    goal = config.get("goal", "")

    template = f"""
### Task Instructions
{instruction}

### Goal
{goal}

### Output Constraints
{output_constraints}

### Output Format
{output_format}

### Goal
{goal}

### Repository Contents to Review:
"""

    def reviewer_node(state: Dict[str, Any]) -> Dict[str, Any]:
        readme_text = state.get("summaries", {}).get("readme.md", "")
        # keywords = state.get("keywords", [])
        # short_summary = state.get("short_summary", "")
        # long_summary = state.get("long_summary", "")

        if not readme_text:
            print("--- WARNING: ReviewerAgent: No README found.")
            return {"review_report": {}}

        prompt = template + "\n" + readme_text

        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=700,
                temperature=0.4,
            )

            output = response.choices[0].message.content
            print("\n--- Reviewer Output ---\n", output)

            state["review_report"] = output
            return state

        except Exception as e:
            print(f"!!! ERROR in ReviewerAgent: {e}")
            state["review_report"] = {}
            return state

    return reviewer_node
