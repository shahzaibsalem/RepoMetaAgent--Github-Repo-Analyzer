import os
from pathlib import Path
# directory containing this file (should be the "code" directory)
BASE_DIR = Path(__file__).resolve().parent
# project root (parent of code/)
PROJECT_ROOT = BASE_DIR.parent

# --- Files in the project structure ---

# gazetteer is inside the same directory as this file (code/)
GAZETTEER_FILE = BASE_DIR / "gazetteer_entities.yaml"

# Path to the .env file (assumed to be in the project root)
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")

# promptConfig.yaml is inside the same directory as this file (code/)
PROMPT_CONFIG_FILE = BASE_DIR / "promptConfig.yaml"

# --- Model/LLM Configuration ---

# Ensure this is a currently supported Groq model
GROQ_MODEL = "llama-3.1-8b-instant" 

# SpaCy model for tag generation
SPACY_MODEL_NAME = "en_core_web_sm"

# Named Entities to ignore in SpaCy extraction
EXCLUDED_SPACY_ENTITY_TYPES = ["DATE", "TIME", "PERCENT", "MONEY", "QUANTITY", "CARDINAL", "ORDINAL"]