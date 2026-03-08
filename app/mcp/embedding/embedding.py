import os
import requests

REQUEST_TIMEOUT_SECONDS = 30

def get_embedding(text_content: str) -> list[float]:
    proxy_url = os.getenv("LLM_PROXY_BASE_URL")

    proxy_api_key = os.getenv("LLM_PROXY_API_KEY")

    if not proxy_url or not proxy_api_key:
        raise ValueError("Set LLM_PROXY_BASE_URL and LLM_PROXY_API_KEY environment variables")

    endpoint = f"{proxy_url}/embeddings"

    headers = {
        "Authorization": f"Bearer {proxy_api_key}",
    }

    payload = {
        "model": "text-embedding-005",
        "input": text_content
    }

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Embedding request failed: {exc}") from exc

    data = response.json()

    return data["data"][0]["embedding"]

