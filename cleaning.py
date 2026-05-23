import os
import json
import re
import time
import pandas as pd
import requests

INPUT_FILE = "REARM.csv"
OUTPUT_FILE = "REARM_final.jsonl"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"
BATCH_SIZE = 5
SLEEP_SECONDS = 6

PROMPT_TEMPLATE = """Stai leggendo dei post/messaggi/commenti in inglese su social network. Esegui due operazioni:

1. Assegna un topic tra: [NATO, Russia, Russia VS Ucraina, Armi nucleari, Propaganda americana, Difesa europea, Riarmo, Altro]
2. Indica se contiene linguaggio offensivo, razzista o di odio (1 = sì, 0 = no)

Rispondi solo in questo formato (senza testo extra):
[
  {"topic": "Russia", "is_toxic": 0},
  {"topic": "NATO", "is_toxic": 1}
]

Analizza i seguenti testi:
{texts}
"""


def get_headers():
    api_token = os.getenv("GROQ_API_KEY")
    if not api_token:
        raise ValueError("La variabile d'ambiente GROQ_API_KEY non è impostata.")

    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }


def batch_texts(texts, batch_size=BATCH_SIZE):
    for i in range(0, len(texts), batch_size):
        yield texts[i:i + batch_size]


def extract_json_array(content):
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def call_llama(batch, headers):
    joined = "\n".join([f'{i + 1}. "{text}"' for i, text in enumerate(batch)])
    prompt = PROMPT_TEMPLATE.replace("{texts}", joined)

    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=30)

        if response.status_code == 429:
            print("Rate limit superato, attendo 10 secondi...")
            time.sleep(10)
            return call_llama(batch, headers)

        if response.status_code == 413:
            print("Errore 413: batch troppo grande.")
            return None

        if response.status_code != 200:
            print(f"Errore API: {response.status_code}")
            return None

        content = response.json()["choices"][0]["message"]["content"]
        return extract_json_array(content)

    except requests.exceptions.RequestException as e:
        print("Errore durante la chiamata API:", e)
        return None
    except (KeyError, IndexError, ValueError) as e:
        print("Errore nel parsing della risposta:", e)
        return None


def load_and_clean_data(input_file):
    df = pd.read_csv(input_file, na_values="N/A")

    columns_to_drop = ["dislikes", "friends", "followers", "following", "posts"]
    existing_columns_to_drop = [col for col in columns_to_drop if col in df.columns]
    df = df.drop(columns=existing_columns_to_drop)

    if "channel_name" in df.columns:
        df["channel_name"] = df["channel_name"].fillna("unknown")

    if "channel_username" in df.columns:
        df["channel_username"] = df["channel_username"].fillna("unknown")

    if "urls" in df.columns:
        df["urls"] = df["urls"].replace("[]", "unknown").fillna("unknown")

    for col in ["reshares", "views", "likes", "replies"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    if "text" in df.columns:
        df = df[df["text"].notna()].reset_index(drop=True)
    else:
        raise ValueError("La colonna 'text' non è presente nel dataset.")

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="mixed", errors="coerce")
        df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return df


def enrich_dataset(df, headers):
    topics = []
    tox_flags = []

    for batch in batch_texts(df["text"].tolist()):
        output = call_llama(batch, headers)

        if output is None or len(output) != len(batch):
            print("Batch scartato o incompleto. Uso valori di default.")
            output = [{"topic": "Altro", "is_toxic": 0} for _ in batch]

        for item in output:
            topics.append(item.get("topic", "Altro"))
            tox_flags.append(item.get("is_toxic", 0))

        time.sleep(SLEEP_SECONDS)

    df["topic"] = topics
    df["is_toxic"] = tox_flags
    return df


def main():
    headers = get_headers()
    df = load_and_clean_data(INPUT_FILE)
    df = enrich_dataset(df, headers)
    df.to_json(OUTPUT_FILE, orient="records", lines=True, force_ascii=False)
    print(f"File JSONL creato: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()