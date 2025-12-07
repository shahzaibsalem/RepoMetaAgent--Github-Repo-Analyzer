import os
from groq import Groq
from typing import Any # Used for the make_llm_extractor_node type hint
from dotenv import load_dotenv
load_dotenv()
# ----------------------
# ⚡️ Groq Client Manager
# ----------------------
class GroqClientManager:
    """Manages the Groq client singleton and model configuration."""
    # NOTE: Set the model to a currently supported, fast one like llama-3.1-8b-instant
    def __init__(self, model="llama-3.3-70b-versatile"):
        api_key = os.getenv("GROQ_API_KEY") # Reads API key from environment variable
        
        # Initialize Groq client
        self.client = Groq(api_key=api_key)
        self.model = model
    
    def get_client(self) -> Groq:
        """Returns the single initialized Groq client object."""
        return self.client
    
    def get_model(self) -> str:
        """Returns the configured model name."""
        return self.model

GROQ_MANAGER = GroqClientManager()