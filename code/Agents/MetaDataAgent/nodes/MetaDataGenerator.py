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

    
def generate_title_short_summary(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    client = groq_manager_instance.get_client()
    model = groq_manager_instance.get_model()

    config = load_prompt_section(PROMPT_CONFIG_FILE , "short_summary_generator")

    llm_model = config.get("llm") or model
    system_role = config.get("role", "")
    instruction = config.get("instruction", "Generate a concise title and a short summary for the given text.")
    output_format = config.get("output_format", '')
    output_contraints = config.get("output_constraints", [])
    goal = config.get("goal", "Provide a short summary in less than 4 lines")


    user_instruction_template = f"""
### Task Instructions
{instruction}

### Output Format
{output_format}

### Output Constraints
{output_contraints}

### Goal
{goal}
### Input Text:
"""
    def title_short_summary_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # text = state.get("summaries", {}).get("readme.md", "")
        text = state.get("readme_md", "")
        if not text:
            print("--- WARNING: No README content found in state.")
            return {"short_summary": ""}

        user_instruction = user_instruction_template + f"\n{text}\n"

        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": user_instruction}
                ],
                max_tokens=500,
                temperature=0.7,
            )

            ai_output = response.choices[0].message.content
            print(f"--- LLM Output for Title and Short Summary ---\n{ai_output}\n")
            state["short_summary"] = ai_output
            return state

        except Exception as e:
            print(f"!!! ERROR: LLM call failed in short summary extraction: {e}")

        state["short_summary"] = ""
        return state
    return title_short_summary_extractor_node 


def generate_long_summary(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    client = groq_manager_instance.get_client()
    model = groq_manager_instance.get_model()

    config = load_prompt_section(PROMPT_CONFIG_FILE , "long_summary_generator")

    llm_model = config.get("llm") or model
    system_role = config.get("role", "You are an AI tag extractor.")
    instruction = config.get("instruction", "Extract relevant tags from the text.")
    output_format = config.get("output_format", '[{"name": "tag", "type": "category"}]')
    output_contraints = config.get("output_constraints", [])
    goal = config.get("goal", "Provide a short summary in less than 4 lines")


    user_instruction_template = f"""
### Task Instructions
{instruction}

### Output Format
{output_format}

### Output Constraints
{output_contraints}

### Goal
{goal}
### Input Text:
"""
    def title_long_summary_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # text = state.get("summaries", {}).get("readme.md", "")
        text = state.get("readme_md", "")
        if not text:
            print("--- WARNING: No README content found in state.")
            return {"long_summary": ""}

        user_instruction = user_instruction_template + f"\n{text}\n"
        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": user_instruction}
                ],
                max_tokens=500,
                temperature=0.7,
            )

            ai_output = response.choices[0].message.content
            print(f"--- LLM Output for Long Summary ---\n{ai_output}\n")
            state["long_summary"] = ai_output
            return state

        except Exception as e:
            print(f"!!! ERROR: LLM call failed in long summary extraction: {e}")
        state["long_summary"] = ""
        return state

    return title_long_summary_extractor_node;  


def generate_topics_seo(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    client = groq_manager_instance.get_client()
    model = groq_manager_instance.get_model()   

    config = load_prompt_section(PROMPT_CONFIG_FILE , "metadata_recommendation_generator")

    llm_model = config.get("llm") or model
    system_role = config.get("role", "")    
    instruction = config.get("instruction", "Generate a list of relevant GitHub topics for the given repository text.")
    output_format = config.get("output_format", '')
    output_contraints = config.get("output_constraints", [])        
    goal = config.get("goal", "")

    user_instruction_template = f"""
### Task Instructions   
{instruction}
### Output Format
{output_format}
### Output Constraints
{output_contraints}
### Goal
{goal}
### Input Text:
"""
    def topics_seo_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # text = state.get("summaries", {}).get("readme.md", "")
        text = state.get("readme_md", "")
        if not text:
            print("--- WARNING: No README content found in state.")
            return {"github_topics": []}

        user_instruction = user_instruction_template + f"\n{text}\n"

        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": user_instruction}
                ],
                max_tokens=500,
                temperature=0.7,
            )

            ai_output = response.choices[0].message.content
            print(f"--- LLM Output for GitHub Topics ---\n{ai_output}\n")
            state["github_topics"] = ai_output
            return state

        except Exception as e:
            print(f"!!! ERROR: LLM call failed in GitHub topics extraction: {e}")
            state["github_topics"] = ""
        return state

    return topics_seo_extractor_node;  

def generate_suggested_title(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:

    client = groq_manager_instance.get_client()
    model = groq_manager_instance.get_model()   

    config = load_prompt_section(PROMPT_CONFIG_FILE , "title_suggestion_generator")

    llm_model = config.get("llm") or model
    system_role = config.get("role", "")    
    instruction = config.get("instruction", "")
    output_format = config.get("output_format", '')
    output_contraints = config.get("output_constraints", [])        
    goal = config.get("goal", "Provide a catchy and relevant title for the repository")

    user_instruction_template = f"""
### Task Instructions   
{instruction}
### Output Format
{output_format}
### Output Constraints
{output_contraints}
### Goal
{goal}
### Input Text:
"""
    def title_suggestion_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # text = state.get("summaries", {}).get("readme.md", "")
        text = state.get("readme_md", "")
        if not text:
            print("--- WARNING: No README content found in state.")
            return {"suggested_title": ""}

        user_instruction = user_instruction_template + f"\n{text}\n"

        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": user_instruction}
                ],
                max_tokens=500,
                temperature=0.7,
            )

            ai_output = response.choices[0].message.content
            print(f"--- LLM Output for Title Suggestion ---\n{ai_output}\n")
            state["suggested_title"] = ai_output
            return state

        except Exception as e:
            print(f"!!! ERROR: LLM call failed in title suggestion extraction: {e}")
        state["suggested_title"] = ""
        return state
    return title_suggestion_extractor_node;
    
   