import yaml
import os
from typing import Dict, Any, Callable, List
import re
import spacy
import json

from pathConfig import GAZETTEER_FILE , SPACY_MODEL_NAME, EXCLUDED_SPACY_ENTITY_TYPES
from groq import Groq
from pathConfig import PROMPT_CONFIG_FILE

from Agents.MetaDataAgent.nodes.GroqManager import GroqClientManager
from pathConfig import GROQ_MODEL

# -----------------------------
# Load YAML Prompt Config
# -----------------------------
def _load_llm_tags_generator_config(file_path: str) -> Dict[str, Any]:
    """
    Loads only the llm_tags_generator configuration from the YAML file.
    Returns a dictionary containing llm, prompt_config, and other relevant fields.
    """
    if not os.path.exists(file_path):
        print(f"!!! ERROR: YAML file not found at: {file_path}")
        return {}

    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            full_config = yaml.safe_load(f)

        agents = full_config.get('tags_generation', {}).get('agents', {})
        llm_tags_generator = agents.get('llm_tags_generator', {})

        llm = llm_tags_generator.get('llm')
        prompt_config = llm_tags_generator.get('prompt_config', {})

        return {
            "llm": llm,
            "role": prompt_config.get("role"),
            "instruction": prompt_config.get("instruction"),
            "output_constraints": prompt_config.get("output_constraints", []),
            "output_format": prompt_config.get("output_format"),
            "style_or_tone": prompt_config.get("style_or_tone", []),
            "goal": prompt_config.get("goal")
        }

    except Exception as e:
        print(f"!!! ERROR: Failed to load llm_tags_generator config: {e}")
        return {}
# -----------------------------
# LLM Extractor Node
# -----------------------------
def make_llm_extractor_node(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns a LangGraph-compatible node that extracts structured tags using a Groq LLM.
    """

    client = groq_manager_instance.get_client()
    model = groq_manager_instance.get_model()
    MAX_LLM_INPUT = 15000

    # Load config for llm_tags_generator
    config = _load_llm_tags_generator_config(PROMPT_CONFIG_FILE)

    llm_model = config.get("llm") or model
    system_role = config.get("role", "You are an AI tag extractor.")
    instruction = config.get("instruction", "Extract relevant tags from the text.")
    output_format = config.get("output_format", '[{"name": "tag", "type": "category"}]')

    # Detect if JSON output is expected
    output_is_json = True if output_format.strip().startswith("[") else False

    # Always enforce JSON requirement for Groq
    system_role += "\nRespond ONLY in valid JSON.\njson"

    # Build user template (also must contain 'json')
    user_instruction_template = f"""
### Task Instructions
{instruction}

Your output MUST be valid JSON.
json

### Output Format (example)
{output_format}

### Input Text:
"""
    def llm_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # text = state.get("summaries", {}).get("readme.md", "")
        text = state.get("readme_md", "")
        print("in llm")
        print(f"text: {text}")
        if not text:
            print("--- WARNING: No README content found in state.")
            return {"llm_keywords": []}
        input_text = text[:MAX_LLM_INPUT]
        final_user_content = f"{user_instruction_template}\n{input_text}"
        llm_keywords: List[str] = []
        try:
            print("--- Running LLM extraction via Groq...")

            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": final_user_content}
            ]

            response_params = {"model": llm_model, "messages": messages}
            if output_is_json:
                response_params["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**response_params)
            response_content = response.choices[0].message.content.strip()

            if isinstance(response_content, str):
                try:
                    response_content = json.loads(response_content)
                except json.JSONDecodeError:
                    print("LLM returned invalid JSON")
                    response_content = {"tags": []}
            
            # Extract tag names
            llm_keywords = [tag["name"] for tag in response_content.get("tags", [])]

        except Exception as e:
            print(f"--- LLM Extraction Error: {type(e).__name__}: {str(e)} ---")
            llm_keywords = []
        
        print("LLM Finished")
        return {"llm_keywords": llm_keywords}

    return llm_extractor_node

# ----------------------
# Gazetteer Extraction Node
# ----------------------

def load_gazetteer_data(file_path: str) -> Dict[str, str]:
    """Loads and returns the Gazetteer data from the YAML file."""
    if not os.path.exists(file_path):
        print(f"!!! ERROR: Gazetteer file not found at: {file_path}")
        return {}
    print("--- Loaded Gazetteer data ---")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def make_gazetteer_tag_generator_node() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    gazetteer = load_gazetteer_data(GAZETTEER_FILE)

    def gazetteer_tag_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
        # text = state.get("summaries", {}).get("readme.md", "")
        text = state.get("readme_md", "")

        if not text:
            return {"gazetteer_keywords": []}
        seen = set()
        entities = []

        for entity_name, entity_type in gazetteer.items():
            pattern = r"\b" + re.escape(entity_name) + r"\b"
            try:
                for _ in re.finditer(pattern, text, re.IGNORECASE):
                    key = (entity_name.lower(), entity_type)
                    if key not in seen:
                        seen.add(key)
                        entities.append(
                            {
                                "name": entity_name.lower().strip(),
                                "type": entity_type.strip(),
                            }
                        )
                        print("success1234")                   
            except re.error as e:
                print(f"Regex error for entity '{entity_name}': {e}")
                continue

        print("Gazetter Finished")    
        print(f"--- Extracted {len(entities)} gazetteer keywords...")
        return {"gazetteer_keywords": entities}

    return gazetteer_tag_generator_node


def make_spacy_extractor_node() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns a LangGraph-compatible node that extracts named entities and key 
    nouns using a pre-loaded SpaCy model. The model is loaded once (closure).
    """
    try:
        # Load the SpaCy model only once when the graph is built
        model = spacy.load(SPACY_MODEL_NAME)
    except OSError:
        # Handle case where the user forgot to download the model
        print(f"!!! WARNING: SpaCy model '{SPACY_MODEL_NAME}' not found. Skipping extraction.")
        print(f"To fix, run: python -m spacy download {SPACY_MODEL_NAME}")
        model = None # Set to None to disable the node gracefully  

    def spacy_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts unique named entities and proper nouns from the content text.
        Updates the 'spacy_keywords' field in the state.
        """
        if not model:
            return {"spacy_keywords": []}
            
  
        # Get the aggregated text content from the state
        # text = state.get("summaries", {}).get("readme.md", "")
        text = state.get("readme_md", "")
        if not text:
             return {"spacy_keywords": []}
             
        doc = model(text)
        seen = set()
        entities = []
        
        # 1. Extract Named Entities (Gazetteer-like technical terms, organizations, etc.)
        for ent in doc.ents:
            # Skip entities that are typically not good keywords (like dates/money)
            if ent.label_ in EXCLUDED_SPACY_ENTITY_TYPES:
                continue
                
            key = ent.text.lower().strip()
            if key not in seen:
                seen.add(key)
                entities.append(key)
        # 2. Extract Key Nouns and Proper Nouns (concepts, objects, features)
        for token in doc:
            # Focus on common nouns (NOUN) and proper nouns (PROPN) longer than 3 characters
            if token.pos_ in ('NOUN', 'PROPN') and len(token.text) > 3:
                key = token.text.lower().strip()
                if key not in seen:
                    seen.add(key)
                    entities.append(key)

        # Final list of unique, sorted keywords from SpaCy
        final_keywords = sorted(entities)
        print("Spacy Finsihed")
        print(f"--- Extracted {len(final_keywords)} keywords via SpaCy/NLP...")
        return {"spacy_keywords": final_keywords}

    return spacy_extractor_node

# ----------------------
# Union and Selector Nodes  

# def union_keywords_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combines and de-duplicates all keyword lists (Regex, SpaCy, Gazetteer, LLM) 
    into the merged 'union_list' field in the state for the selector node.
    """
    
    # Safely retrieve lists from the state, defaulting to an empty list if a key is missing
    print("--- Union Keywords Node Invoked ---")
    regex_k = state.get("regex_keywords", [])
    spacy_k = state.get("spacy_keywords", [])
    gazetteer_k = state.get("gazetteer_keywords", [])
    llm_k = state.get("llm_keywords", []) 
    
    # Concatenate all lists
    all_keywords = regex_k + spacy_k + gazetteer_k + llm_k
    
    # Use a set for de-duplication, and convert to a list of strings
    unique_keywords = sorted(list(set(all_keywords)))
    
    # NOTE: We store the raw union list in a new field for the next node
    print(f"--- 3e. Combined and cleaned list of {len(unique_keywords)} keywords for selection...")
    print("Callnig assign_tag_types now")
    assign_tag_types(unique_keywords)

    print("Union Finished") 
    
    return {"union_list": unique_keywords}

def union_keywords_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("--- Union Keywords Node Invoked ---")

    # regex_k = state.get("regex_keywords", [])
    spacy_k = state.get("spacy_keywords", [])
    gazetteer_k = state.get("gazetteer_keywords", [])
    llm_k = state.get("llm_keywords", [])

    # Normalize all keyword lists into pure strings
    def normalize_list(lst):
        normalized = []
        for item in lst:
            if isinstance(item, dict):
                # pick only the name field
                normalized.append(item.get("name", "").lower())
            elif isinstance(item, str):
                normalized.append(item.lower())
        return normalized

    # regex_k = normalize_list(regex_k)
    spacy_k = normalize_list(spacy_k)
    gazetteer_k = normalize_list(gazetteer_k)
    llm_k = normalize_list(llm_k)

    # Combine and dedupe
    all_keywords = spacy_k + gazetteer_k + llm_k
    unique_keywords = sorted(list(set(all_keywords)))

    print(f"--- Combined & cleaned {len(unique_keywords)} keywords ---")
    print("Calling assign_tag_types now...")

    return {"union_list": unique_keywords}


# ----------------------
# LLM Selector Node
# -----------------------------
# Load tags_selector Config
# -----------------------------
def load_tags_selector_config(file_path: str) -> Dict[str, Any]:
    """
    Loads and returns the 'tags_selector' portion of the YAML config.
    """
    if not os.path.exists(file_path):
        print(f"!!! ERROR: Config file not found at: {file_path}")
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        full_config = yaml.safe_load(f)

    # Navigate to tags_selector agent
    selector_config = (
        full_config.get("tags_generation", {})
                   .get("agents", {})
                   .get("tags_selector", {})
    )
    return selector_config

# ---------------------------
# 2. Selector node function
# ---------------------------
def make_selector_node(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Creates a LangGraph-compatible selector node that uses the tags_selector LLM
    to pick the most important tags from a candidate list.
    """

    # 2a. Initialize Groq client once (closure)
    client = groq_manager_instance.get_client()
    model = groq_manager_instance.get_model()

    # 2b. Load tags_selector config
    selector_config = load_tags_selector_config(PROMPT_CONFIG_FILE)

    role = selector_config.get("prompt_config", {}).get("role", "A curator who selects the most important tags.")
    instruction = selector_config.get("prompt_config", {}).get("instruction", "Select the best tags from the list.")
    output_format = selector_config.get("prompt_config", {}).get("output_format", '[{"name": "Tag","type": "Tag Type"}]')
    max_tags = selector_config.get("max_tags", 10)

    # Build the user instruction template
    user_instruction_template = f"""
{instruction}

The maximum number of tags to return is {max_tags}.

### Candidate Tags
[CANDIDATE_TAGS_PLACEHOLDER]

### Required Output Format (Strict JSON)
{output_format}
""".strip()

    system_role_full = f"{role}. Respond ONLY with valid JSON matching the specified structure."

    # 2c. Define the selector node
    def selector_node(state: Dict[str, Any]) -> Dict[str, Any]:
        print("--- Selector Node Invoked ---")
        union_list: List[str] = state.get("union_list", [])
        content_text: str = state.get("summaries", {}).get("readme.md", "")

        if not union_list:
            print("--- WARNING: No candidate tags found in state.")
            return {"keywords": []}

        # Prepare candidate list for the prompt
        candidate_tags_str = "\n".join(f"- {tag}" for tag in union_list)
        final_instruction = user_instruction_template.replace(
            "[CANDIDATE_TAGS_PLACEHOLDER]", candidate_tags_str
        )

        final_user_message = (
            f"{final_instruction}\n\n"
            f"### Original Text (truncated):\n{content_text[:5000]}..."
        )

        print("\n--- Running LLM Selector (Curator) ---")

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_role_full},
                    {"role": "user", "content": final_user_message}
                ]
            )

            print("--- LLM Selector Response Received ---")
            print(f"--- Full LLM Selector Response: {response} ---")

            raw_content = response.choices[0].message.content.strip()

            print(f"--- Raw LLM Selector Output:\n{raw_content}\n--- End of Output1 ---")

            # Remove ```json wrappers if present
            if raw_content.startswith("```"):
                raw_content = raw_content.strip("```").replace("json", "", 1).strip()

            # Parse JSON safely
            data = json.loads(raw_content)

            print(f"--- Parsed LLM Selector Data: {data} --- End of output2s ---")

            # Handle both dict and list outputs from LLM
            if isinstance(data, dict) and "tags" in data:
                print("--- LLM Selector returned a dictionary with 'tags' key ---")
                # Extract tags from the dictionary
                tag_items = data["tags"]
            elif isinstance(data, list):
                tag_items = data
            else:
                tag_items = []

            # Extract only valid tag names
            final_keywords = [
                t["name"].strip().lower()
                for t in tag_items
                if isinstance(t, dict) and t.get("name") and len(t["name"].strip()) > 2
            ]

        except Exception as e:
            print(f"--- LLM Selector Error: {type(e).__name__}: {e} ---")
            final_keywords = []

        print(f"--- Selected {len(final_keywords)} final keywords ---")
        print("Selector Finished")
        # final_keywords_with_types = assign_tag_types(final_keywords)
        return {"keywords": final_keywords}

    return selector_node





# -----------------------------
# Standalone Tag Type Assigner Function
# ----------------------------- 

def load_tag_type_assigner_config(file_path: str) -> Dict[str, Any]:
    """
    Loads only the 'tag_type_assigner' configuration from YAML.
    Returns role, instruction, output_format, etc.
    """
    if not os.path.exists(file_path):
        print(f"!!! ERROR: YAML file not found at: {file_path}")
        return {}

    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            full_config = yaml.safe_load(f)

        agents = full_config.get('tags_generation', {}).get('agents', {})
        tag_assign_cfg = agents.get('tag_type_assigner', {})

        llm = tag_assign_cfg.get('llm')
        prompt_config = tag_assign_cfg.get('prompt_config', {})

        return {
            "llm": llm,
            "role": prompt_config.get("role"),
            "instruction": prompt_config.get("instruction"),
            "output_constraints": prompt_config.get("output_constraints", []),
            "output_format": prompt_config.get("output_format"),
            "style_or_tone": prompt_config.get("style_or_tone", []),
            "goal": prompt_config.get("goal"),
        }

    except Exception as e:
        print(f"!!! ERROR: Failed to load tag_type_assigner config: {e}")
        return {}



def assign_tag_types(
    keywords: List[str],
) -> List[Dict[str, str]]:
    """
    Assigns tag types to keywords using:
      - Groq LLM
      - YAML config (tag_type_assigner)
    """
    # Init Groq client
    GROQ_MANAGER = GroqClientManager(model=GROQ_MODEL)
    client = GROQ_MANAGER.get_client()

    # Load tag-type-assigner config
    cfg = load_tag_type_assigner_config(PROMPT_CONFIG_FILE)

    if not cfg:
        print("!!! ERROR: tag_type_assigner config empty.")
        return []

    llm_model = cfg.get("llm", GROQ_MANAGER.get_model())
    system_role = cfg["role"]
    instruction = cfg["instruction"]
    output_format = cfg["output_format"]
    output_constraints = cfg["output_constraints"]
    style_or_tone = cfg["style_or_tone"]
    goal = cfg["goal"]

    # USER prompt template
    USER_TEMPLATE = f"""
### Task Instructions
{instruction}

### Style or Tone
{style_or_tone}

### Output Constraints
{output_constraints}

### Output Format
Return JSON exactly like this:

{output_format}

### goal
{goal}

### Following are the Input Tags
"""

    # Convert keywords → [{"name": "..."}]
    keyword_items = [{"name": kw} for kw in keywords]

    user_prompt = USER_TEMPLATE + json.dumps(keyword_items, indent=2)

    messages = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": user_prompt},
    ]

    print("--- Running Tag Type Assigner (Groq)...")

    response = client.chat.completions.create(
        model=llm_model,
        messages=messages,
        response_format={"type": "json_object"},
    )

    response_content = response.choices[0].message.content.strip()

    # Parse JSON
    try:
        parsed = json.loads(response_content)

        if isinstance(parsed, dict) and "tags" in parsed:
            print("--- Successfully assigned tag types.")
            print(f"--- Assigned Tags: {parsed['tags']} ---")
            return parsed["tags"]

        if isinstance(parsed, list):
            print("--- Successfully assigned tag types.")
            print(f"--- Assigned Tags: {parsed} ---")
            return parsed

        print("--- Unexpected LLM format — returned empty.")
        return []

    except Exception as e:
        print(f"--- JSON parse error: {type(e).__name__}: {e}")
        return []
