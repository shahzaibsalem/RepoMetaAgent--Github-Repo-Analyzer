import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# --- Files in the project structure ---

# Path to the gazetteer YAML file (assumed to be in the 'src' directory itself)
GAZETTEER_FILE = os.path.join(BASE_DIR, "gazetteer_entities.yaml")

# Path to the .env file (assumed to be in the project root)
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")

# Path to the prompt configuration YAML file
PROMPT_CONFIG_FILE = os.path.join(PROJECT_ROOT, "promptConfig.yaml")

# If you have a separate Database folder inside src/
# DATABASE_DIR = os.path.join(BASE_DIR, "Database")
# PROMPT_CONFIG_FILE = os.path.join(DATABASE_DIR, "promptConfig.yaml")

# --- Model/LLM Configuration ---

# Ensure this is a currently supported Groq model
GROQ_MODEL = "llama-3.1-8b-instant" 

# SpaCy model for tag generation
SPACY_MODEL_NAME = "en_core_web_sm"

# Named Entities to ignore in SpaCy extraction
EXCLUDED_SPACY_ENTITY_TYPES = ["DATE", "TIME", "PERCENT", "MONEY", "QUANTITY", "CARDINAL", "ORDINAL"]