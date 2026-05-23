mapping = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "data_type": {"type": "keyword"},
            "channel_username": {"type": "keyword"},
            "channel_name": {"type": "keyword"},
            "username": {"type": "keyword"},
            "text": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword", "ignore_above": 256}
                }
            },
            "timestamp": {"type": "date"},
            "site": {"type": "keyword"},
            "reshares": {"type": "integer"},
            "views": {"type": "integer"},
            "likes": {"type": "integer"},
            "replies": {"type": "integer"},
            "urls": {"type": "keyword"},
            "topic": {"type": "keyword"},
            "is_toxic": {"type": "integer"}
        }
    }
}

def build_prompt(question):
    return f"""
Sei un assistente intelligente in una web app Streamlit che aiuta l'utente ad analizzare il dataset REARM, un dataset indicizzato in Elasticsearch
che contiene messaggi/post/commenti DISINFORMATIVI in inglese (su telegram e altri social) circa il riarmo dell'Europa, devi guidare l'utente che
fa la domanda nell'interpretazione di questi dati.
Quindi devi fare sia un ragionamento di come hai risposto alla domanda sia estrarre i parametri necessari per costruire un url kibana che aggiornerà 
una dashboard che verrà visualizzata e aggiornata in base alla tua risposta.

Struttura del dataset:
{mapping}

Il dataset si chiama `rearm.jsonl`, si tratta di messaggi,post o commenti prelevati da siti("4chan","telegram","gab") nell'ambito della
disinformazione sul riarmo dell'Europa, ecco la struttura:

- id: identificativo univoco del post (es: "pol_498987666") [tipo: keyword]  
- data_type: tipo di contenuto: 'comment', 'post', 'message' [keyword]  
- channel_username: nome utente del canale, 'unknown' se mancante [keyword]  
- channel_name: nome del canale (es: "pol") [keyword]  
- username: autore del post (es: "Anonymous") [keyword]  
- text: contenuto testuale del messaggio [text, full-text search]  
- timestamp: data e ora del post, in formato ISO (es: "2023-07-04T13:38:56") [date]  
- site: piattaforma di provenienza, tra '4chan', 'Telegram', 'gab' [keyword]  
- reshares: numero di condivisioni [integer]  
- views: numero di visualizzazioni [integer]  
- likes: numero di like [integer]  (range 0-17)
- replies: numero di risposte [integer]  
- urls: URL collegati al post (se presenti) [keyword]
- is_toxic : post con contenuti offensivi, razzisti, etc (1/0) [integer]
- topic: tipo di argomento del post: [NATO, Russia, Russia VS Ucraina, Armi nucleari, Propaganda americana, Difesa europea, Riarmo, Altro] (keyword)

⚠️ Rispetta esattamente la seguente struttura nel tuo output (le intestazioni devono iniziare la riga e NON devono essere modificate):

1. Ragionamento:
Spiega quali campi hai usato e perché. Non saltare questa sezione.

2. Parametri Kibana:
- Campo: [nome campo da filtrare, oppure 'None']
- Valore: [valore del filtro, oppure 'None']
- Intervallo temporale: from [data_inizio] to [data_fine]
  (usa from 2025-02-28 to 2025-03-24 se la domanda non specifica un intervallo, ma non scrivere 'default' nel testo)

3. Query Elasticsearch:
Scrivi una query JSON compatibile con Elasticsearch.

Esempio:

1. Ragionamento:
Mi baso sul campo "site" perché l’utente vuole analizzare i post da telegram.

2. Parametri Kibana:
- Campo: site
- Valore: telegram
- Intervallo temporale: from 2025-02-28 to 2025-03-24

3. Query Elasticsearch:
{{
  "query": {{
    "term": {{
      "site": "telegram"
    }}
  }}
}}

Domanda dell'utente:
"{question}"
"""
