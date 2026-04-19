from langchain_openai import ChatOpenAI
from config import VOYAGER_MODEL_NAME, VOYAGER_BASE_URL, VOYAGER_API_KEY

def get_llm(temperature=0.1, max_retries=3):
    print(f"--- Connecting to ASU Voyager API: {VOYAGER_MODEL_NAME} ---")
    if not VOYAGER_API_KEY:
        raise ValueError("CRITICAL: VOYAGER_API_KEY not found. Please check your .env file.")
    
    return ChatOpenAI(
        model=VOYAGER_MODEL_NAME,
        openai_api_key=VOYAGER_API_KEY,
        openai_api_base=VOYAGER_BASE_URL,
        temperature=temperature, 
        max_retries=max_retries
    )
