import yaml
import os
from typing import Dict, Any, Callable, List
import re
import spacy
import json

from ....pathConfig import GAZETTEER_FILE , SPACY_MODEL_NAME, EXCLUDED_SPACY_ENTITY_TYPES
from groq import Groq
from ....pathConfig import PROMPT_CONFIG_FILE


# ----------------------
# LLM Extraction Node
# ----------------------
def _load_prompt_config(file_path: str) -> Dict[str, Any]:
    """Loads and returns the prompt configuration from the YAML file."""
    try:
        with open(file_path, 'r') as f:
            full_config = yaml.safe_load(f)
        
        # Access the specific configuration block: tags_generation -> agents -> llm_tags_generator
        agent_config = full_config.get('tags_generation', {}).get('agents', {}).get('llm_tags_generator', {})
        tag_types = full_config.get('tags_generation', {}).get('tag_types', [])
        
        return {
            "prompt_config": agent_config.get("prompt_config", {}),
            "tag_types": tag_types,
            "llm_model_yaml": agent_config.get("llm")
        }
        
    except Exception as e:
        print(f"!!! ERROR: Could not load prompt config from {file_path}: {e}")
        return {}


def make_llm_extractor_node(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns a LangGraph-compatible node that extracts structured tags using a Groq LLM.
    The Groq client and the full YAML prompt configuration are loaded once (closure).
    """
    # --- Closure Setup (Runs Once) ---
    client: Groq = groq_manager_instance.get_client()
    model: str = groq_manager_instance.get_model()
    MAX_LLM_INPUT = 15000 
    
    # Load and process Configuration
    config = _load_prompt_config(PROMPT_CONFIG_FILE)
    
    # Check if config loaded successfully
    if not config or 'prompt_config' not in config:
        print("!!! LLM PROMPT CONFIG ERROR: Using fallback prompt.")
        system_role = "You are a concise expert analyst. Return ONLY a comma-separated list of keywords, nothing else."
        user_instruction_template = "Analyze the content and return 15 key technical keywords.\n\nContent:\n"
        output_is_json = False
    else:
        # Extract and format required fields from YAML
        p_config = config['prompt_config']
        tag_types_list = [f"- {t['name']}: {t['description']}" for t in config['tag_types']]
        
        system_role = p_config.get('role', 'An analyst.')
        instruction = p_config.get('instruction', 'Extract relevant tags.')
        output_format = p_config.get('output_format', 'Return JSON.')
        
        # The System Role will carry the identity and required output format
        system_role_full = f"{system_role}. Your output MUST strictly adhere to the following JSON structure: {output_format}"
        
        # The User Instruction Template includes detailed instructions and tag types
        user_instruction_template = f"""
### Task Instructions
{instruction.strip()}

### Tag Types List
{'\n'.join(tag_types_list)}

### Input Text:
"""
        output_is_json = True
        
        # Overwrite model if specified in YAML (optional but good practice)
        if config.get('llm_model_yaml'):
            model = config['llm_model_yaml']


    def llm_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts structured keywords using the Groq LLM based on the YAML prompt.
        """
        text = state.get("content_text", "")
        if not text:
            return {"llm_keywords": []}
            
        input_text = text[:MAX_LLM_INPUT]
        
        # Construct the final user message with the content
        final_user_content = f"{user_instruction_template}\n{input_text}"
        
        llm_keywords: List[str]
        try:
            print("--- 3d. Running LLM extraction via Groq...")
            
            messages = [
                {"role": "system", "content": system_role_full},
                {"role": "user", "content": final_user_content}
            ]
            
            response_params = {"model": model, "messages": messages}
            if output_is_json:
                response_params["response_format"] = {"type": "json_object"} 
            
            response = client.chat.completions.create(**response_params)
            
            response_content = response.choices[0].message.content.strip()
            
            if output_is_json:
                # Parse the JSON array of objects
                tag_list = json.loads(response_content)
                
                # Extract only the 'name' field and clean/lowercase it
                llm_keywords = [
                    tag.get('name', '').strip().lower() 
                    for tag in tag_list 
                    if tag.get('name') and len(tag.get('name').strip()) > 2
                ]
            else:
                # Fallback path (should not happen if YAML is present)
                llm_keywords = [
                    kw.strip().lower() 
                    for kw in response_content.split(',') 
                    if kw.strip() and len(kw.strip()) > 2
                ]
            
        except Exception as e:
            print(f"--- LLM Extraction Error: {type(e).__name__}: {str(e)} ---")
            llm_keywords = []
            
        print(f"--- Extracted {len(llm_keywords)} keywords via LLM.")
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
    """
    Returns a LangGraph-compatible node that extracts tags based on a Gazetteer file.
    The Gazetteer data is loaded once when the graph is built (closure).
    """
    # 1. Load the data into the closure
    gazetteer_map = load_gazetteer_data(GAZETTEER_FILE)
    gazetteer_terms = list(gazetteer_map.keys())

    # 2. Compile a single, efficient regex pattern for all terms
    # Sort by length descending to match longer phrases first (e.g., "decision tree" before "tree")
    gazetteer_terms.sort(key=len, reverse=True)
    
    # Create a pattern that matches any of the terms as whole words/phrases
    # The 're.escape' handles special characters in terms
    pattern = r'\b(' + '|'.join(re.escape(term) for term in gazetteer_terms) + r')\b'
    term_regex = re.compile(pattern, re.IGNORECASE)

    def gazetteer_tag_generator_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scans the repository content text for any matching terms defined in the Gazetteer.
        The result is stored in the 'gazetteer_keywords' state field.
        """
        # Assume 'content_text' is the field holding the aggregated repo content
        text = state.get("content_text", "")
        if not text:
            return {"gazetteer_keywords": []}

        matches = term_regex.findall(text)
        
        # Get unique, lowercased matches
        extracted_tags = sorted(list(set([
            match.lower() 
            for match in matches
            if match.strip()
        ])))
        
        print(f"--- Extracted {len(extracted_tags)} tags from Gazetteer: {extracted_tags[:5]}...")

        # Returns a dict to update the LangGraph state
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

    def spacy_extractor_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts unique named entities and proper nouns from the content text.
        Updates the 'spacy_keywords' field in the state.
        """
        if not model:
            return {"spacy_keywords": []}
            
        # Get the aggregated text content from the state
        text = state.get("content_text", "")
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
def make_selector_node(groq_manager_instance: Any) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns a node that uses the LLM (Groq) as a Curator to select the best 
    tags from the merged union list, based on the 'tags_selector' prompt config.
    """
    # --- Closure Setup (Runs Once) ---
    client = groq_manager_instance.get_client()
    model = groq_manager_instance.get_model()
    
    # Load and process Configuration for the 'tags_selector' agent
    config = _load_prompt_config(PROMPT_CONFIG_FILE) # Reuse the existing loader
    
    # Access the specific configuration block: tags_generation -> agents -> tags_selector
    selector_config = config.get('tags_generation', {}).get('agents', {}).get('tags_selector', {})
    
    # Extract prompt fields
    prompt_config = selector_config.get('prompt_config', {})
    max_tags = config.get('tags_generation', {}).get('max_tags', 10) # Max 10 tags
    
    system_role = prompt_config.get('role', 'A curator who selects the most important tags.')
    instruction = prompt_config.get('instruction', 'Select the best tags.')
    output_format = prompt_config.get('output_format', 'Return JSON.')
    
    # Construct the User Instruction Template
    user_instruction_template = f"""
{instruction.strip()}

The maximum number of tags to return is {max_tags}.

### Candidate Tags
[CANDIDATE_TAGS_PLACEHOLDER]

### Required Output Format (Strict JSON)
{output_format}
"""
    # The System Role will carry the identity and required output format
    system_role_full = f"{system_role}. Your final response MUST strictly adhere to the JSON structure provided in the user message."


    def selector_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submits the merged list (union_list) and the content text to the LLM for curation.
        """
        union_list: List[str] = state.get("union_list", [])
        content_text: str = state.get("content_text", "")
        
        if not union_list:
            return {"keywords": []}
            
        # Format the list of candidates for the prompt
        candidate_tags_str = "\n".join([f"- {tag}" for tag in union_list])
        
        # Insert the candidates into the template
        final_instruction = user_instruction_template.replace(
            "[CANDIDATE_TAGS_PLACEHOLDER]", candidate_tags_str
        )
        
        # Combine instruction with original text and optional memo (not used here)
        final_user_content = f"{final_instruction}\n\n### Original Text:\n{content_text[:5000]}..." # Truncate text
        
        try:
            print("--- 3f. Running LLM Selector (Curator) to pick best tags...")
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_role_full},
                    {"role": "user", "content": final_user_content}
                ],
                response_format={"type": "json_object"} 
            )
            
            # The response content will be a JSON string containing the final tags
            json_response = response.choices[0].message.content.strip()
            
            # Parse the JSON array of objects
            final_tag_list = json.loads(json_response)
            
            # Extract only the 'name' field (we lose the 'type' here, but get the best selection)
            final_keywords = [
                tag.get('name', '').strip().lower() 
                for tag in final_tag_list 
                if tag.get('name') and len(tag.get('name').strip()) > 2
            ]
            
        except Exception as e:
            print(f"--- LLM Selector Error: {type(e).__name__}: {str(e)} ---")
            final_keywords = []
            
        print(f"--- Selected {len(final_keywords)} final keywords.")
        # The final result is stored in the 'keywords' field
        return {"keywords": final_keywords}

    return selector_node