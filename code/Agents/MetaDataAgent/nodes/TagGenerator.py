import yaml
import os
from typing import Dict, Any, Callable, List
import re
import spacy
import json

from pathConfig import GAZETTEER_FILE , SPACY_MODEL_NAME, EXCLUDED_SPACY_ENTITY_TYPES
from groq import Groq
from pathConfig import PROMPT_CONFIG_FILE

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
    system_role = config.get("role", "An analyst")
    instruction = config.get("instruction", "Extract relevant tags from the text.")
    output_format = config.get("output_format", "[{\"name\": Tag, \"type\": Tag Type}]")
    output_is_json = True if output_format.strip().startswith("[") else False
    print("hello this is text")
    # User instruction template
    user_instruction_template = f"""
       ### Task Instructions
       {instruction.strip()}
       
       ### Input Text:
       """
    def llm_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        text = state.get("summaries", {}).get("readme.md", "")
        print("hello this is text")
        if not text:
            print("--- WARNING: No README content found in state.")
            return {"llm_keywords": []}
        print("hello this is after if text")
        input_text = text[:MAX_LLM_INPUT]
        print("hello this is also after if text")
        final_user_content = f"{user_instruction_template}\n{input_text}"

        print("Final User Content prepared for LLM extraction.")
        print(final_user_content)

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

            if output_is_json:
                try:
                    tag_list = json.loads(response_content)
                    llm_keywords = [
                        tag.get('name', '').strip().lower()
                        for tag in tag_list
                        if tag.get('name') and len(tag.get('name').strip()) > 2
                    ]
                except Exception as e:
                    print(f"--- JSON Parsing Error: {type(e).__name__}: {e}")
                    llm_keywords = []
            else:
                # fallback: comma-separated string
                llm_keywords = [
                    kw.strip().lower()
                    for kw in response_content.split(',')
                    if kw.strip() and len(kw.strip()) > 2
                ]

        except Exception as e:
            print(f"--- LLM Extraction Error: {type(e).__name__}: {str(e)} ---")
            llm_keywords = []

        print(f"--- Extracted {len(llm_keywords)} keywords via LLM.")
        print(f"The llm keywords are: {llm_keywords[:10]}...")
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
    
    with open(file_path, 'r') as f:
        # Load the YAML data, which is already key: value (term: type)
        data = yaml.safe_load(f)
    return data

def make_gazetteer_tag_generator_node() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    gazetteer_map = load_gazetteer_data(GAZETTEER_FILE)
    gazetteer_terms = [term.strip() for term in gazetteer_map.keys() if term.strip()]
    gazetteer_terms.sort(key=len, reverse=True)  # longer phrases first
    pattern = '(' + '|'.join(re.escape(term) for term in gazetteer_terms) + ')'
    term_regex = re.compile(pattern, re.IGNORECASE)
    print("I am here!")
    def gazetteer_tag_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
        text = state.get("summaries", {}).get("readme.md", "")
        print("I am here!")

        if not text:
            return {"gazetteer_keywords": []}
        
        print("I am here!")      

        matches = term_regex.findall(text)
        extracted_tags = sorted(set(match.lower() for match in matches if match.strip()))
        print(f"--- Extracted {len(extracted_tags)} tags: {extracted_tags[:10]}...")

        print("I am here!")

        return {"gazetteer_keywords": extracted_tags}

    return gazetteer_tag_generator_node


def make_spacy_extractor_node() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns a LangGraph-compatible node that extracts named entities and key 
    nouns using a pre-loaded SpaCy model. The model is loaded once (closure).
    """
    try:
        # Load the SpaCy model only once when the graph is built
        model = spacy.load(SPACY_MODEL_NAME)
        print(f"--- Loaded SpaCy model: {SPACY_MODEL_NAME} ---")
    except OSError:
        # Handle case where the user forgot to download the model
        print(f"!!! WARNING: SpaCy model '{SPACY_MODEL_NAME}' not found. Skipping extraction.")
        print(f"To fix, run: python -m spacy download {SPACY_MODEL_NAME}")
        model = None # Set to None to disable the node gracefully
    print("I am here!")    

    def spacy_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts unique named entities and proper nouns from the content text.
        Updates the 'spacy_keywords' field in the state.
        """
        print("I am here!") 
        if not model:
            return {"spacy_keywords": []}
            

        print("I am here!")     
        # Get the aggregated text content from the state
        text = state.get("summaries", {}).get("readme.md", "")
        if not text:
             return {"spacy_keywords": []}
             
        doc = model(text)
        seen = set()
        entities = []

        print("I am here!") 
        
        # 1. Extract Named Entities (Gazetteer-like technical terms, organizations, etc.)
        for ent in doc.ents:
            # Skip entities that are typically not good keywords (like dates/money)
            if ent.label_ in EXCLUDED_SPACY_ENTITY_TYPES:
                continue
                
            key = ent.text.lower().strip()
            if key not in seen:
                seen.add(key)
                entities.append(key)
        print("I am here!") 
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
        print("I am here!") 
        print(f"--- Extracted {len(final_keywords)} keywords via SpaCy/NLP...")
        return {"spacy_keywords": final_keywords}

    return spacy_extractor_node

# ----------------------
# Union and Selector Nodes  

def union_keywords_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combines and de-duplicates all keyword lists (Regex, SpaCy, Gazetteer, LLM) 
    into the merged 'union_list' field in the state for the selector node.
    """
    
    # Safely retrieve lists from the state, defaulting to an empty list if a key is missing
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
{instruction.strip()}

The maximum number of tags to return is {max_tags}.

### Candidate Tags
[CANDIDATE_TAGS_PLACEHOLDER]

### Required Output Format (Strict JSON)
{output_format}
""".strip()

    system_role_full = f"{role}. Respond ONLY with valid JSON matching the specified structure."

    # 2c. Define the selector node
    def selector_node(state: Dict[str, Any]) -> Dict[str, Any]:
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

            raw_content = response.choices[0].message.content.strip()

            # Remove ```json wrappers if present
            if raw_content.startswith("```"):
                raw_content = raw_content.strip("```").replace("json", "", 1).strip()

            # Parse JSON safely
            data = json.loads(raw_content)

            # Handle both dict and list outputs from LLM
            if isinstance(data, dict) and "tags" in data:
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
        return {"keywords": final_keywords}

    return selector_node