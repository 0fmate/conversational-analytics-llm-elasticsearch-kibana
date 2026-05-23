import os
import requests

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"


def call_llm(prompt):
    api_token = os.getenv("GROQ_API_KEY")

    if not api_token:
        return "Errore: variabile d'ambiente GROQ_API_KEY non impostata."

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "Sei un esperto di analisi dati con Elasticsearch e Kibana. Rispondi nel formato richiesto."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.4,
        "max_tokens": 1000
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Errore durante la chiamata al modello: {e}"
    except (KeyError, IndexError, ValueError) as e:
        return f"Errore nel parsing della risposta del modello: {e}"