import os
from typing import List, Dict, Any
from googleapiclient.discovery import build
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def google_search(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """
    Perform Google Custom Search.
    
    Args:
        query: Search query string
        num_results: Number of results to return (max 10 per API call)
    
    Returns:
        List of search results with title, link, snippet
    """
    try:
        service = build(
            "customsearch", "v1",
            developerKey=os.getenv("GOOGLE_API_KEY")
        )
        
        result = service.cse().list(
            q=query,
            cx=os.getenv("GOOGLE_CSE_ID"),
            num=min(num_results, 10)
        ).execute()
        
        search_results = []
        for item in result.get('items', []):
            search_results.append({
                'title': item.get('title'),
                'link': item.get('link'),
                'snippet': item.get('snippet'),
                'source': item.get('displayLink', 'Unknown')
            })
        
        return search_results
    
    except Exception as e:
        print(f"Google Search Error: {e}")
        return []


def call_openai(
    prompt: str,
    model: str = None,
    temperature: float = None,
    seed: int = None,
    max_tokens: int = 2000
) -> str:
    """
    Call OpenAI API with standardized settings.
    
    Args:
        prompt: The prompt to send
        model: Model name (defaults to env var)
        temperature: Sampling temperature (defaults to env var)
        seed: Random seed for reproducibility (defaults to env var)
        max_tokens: Maximum tokens to generate
    
    Returns:
        Generated text response
    """
    model = model or os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    temperature = temperature if temperature is not None else float(os.getenv("TEMPERATURE", "0.7"))
    seed = seed if seed is not None else int(os.getenv("SEED", "42"))
    
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful research assistant that provides accurate, well-cited information."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            seed=seed,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return f"Error: {str(e)}"


def get_model_settings() -> Dict[str, Any]:
    """Get current model settings for logging."""
    return {
        "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        "temperature": float(os.getenv("TEMPERATURE", "0.7")),
        "seed": int(os.getenv("SEED", "42"))
    }


def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = os.path.join("backend", "prompts", f"{prompt_name}.txt")
    
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Prompt file {prompt_path} not found")
        return ""
