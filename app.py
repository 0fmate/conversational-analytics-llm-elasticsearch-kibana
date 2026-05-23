import streamlit as st
from prompts import build_prompt
from llm_client import call_llm
from kibana_url import build_kibana_url
import json
import re


st.set_page_config(page_title="Conversational Analytics - Fake News", layout="wide")

# === SIDEBAR ===
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/artificial-intelligence.png", width=60)
    st.title("Conversational Analytics")
    st.markdown("📊 Analisi interattiva della disinformazione sul riarmo europeo con LLM e ELK Stack.")
    st.markdown("---")
    st.markdown("👨‍💻 *Autore: Davide D'Amico  \n🎓 *Tesi triennale in Basi di Dati, Statistica per i Big Data*")
    st.markdown("---")
    
    st.markdown("### 🔁 Esempi rapidi")
    example_1 = st.button("Quali sono i post tossici su Telegram con topic Riarmo?")
    example_2 = st.button("Quali sono i post con più di 10 views con topic NATO?")
    example_3 = st.button("Quali sono i post sul topic Russia vs Ucraina dal 1 al 10 marzo 2025?")
    example_4 = st.button("Quali sono i post con più di 1000 views con topic Riarmo")
    example_5 = st.button("Quali sono i post tossici con più di 5 likes?")



# === HEADER ===
st.markdown("""
<div style='display: flex; align-items: center; gap: 10px;'>
    <img src="https://img.icons8.com/color/48/000000/artificial-intelligence.png" width="40"/>
    <h1 style='margin: 0; font-size: 1.8em;'>Conversational Analytics • Disinformazione sul riarmo dell'Europa</h1>
</div>
""", unsafe_allow_html=True)

st.markdown(
    "<p style='font-size: 1.1em; color: gray;'>Un sistema conversazionale basato su LLM per esplorare, filtrare e visualizzare dati testuali legati alla disinformazione.</p>",
    unsafe_allow_html=True
)

st.markdown("---")
st.markdown("### 🔎 Fai una domanda sul dataset")

# === INPUT DINAMICO ===
default_prompt = ""
if example_1:
    default_prompt = "Quali sono i post tossici su Telegram con topic Riarmo?"
elif example_2:
    default_prompt = "Quali sono i post con più di 10 views con topic NATO?"
elif example_3:
    default_prompt = "Quali sono i post sul topic Russia vs Ucraina dal 1 al 10 marzo 2025?"
elif example_4:
    default_prompt = "Quali sono i post con più di 1000 views con topic Riarmo?"
elif example_5:
    default_prompt = "Quali sono i post tossici con più di 5 likes?"    

user_question = st.text_input(
    label="",
    value=default_prompt,
    placeholder="Es. Quali sono i post con contenuti tossici?",
    label_visibility="collapsed"
)

# === RISPOSTA LLM ===
if user_question:
    prompt = build_prompt(user_question)
    llm_output = call_llm(prompt)

    try:
        lines = llm_output.splitlines()
        section_idx = {"Ragionamento": None, "Parametri Kibana": None, "Query Elasticsearch": None}

        for i, line in enumerate(lines):
            clean_line = line.strip().replace("*", "")
            if clean_line.startswith("1. Ragionamento:"):
                section_idx["Ragionamento"] = i
            elif clean_line.startswith("2. Parametri Kibana:"):
                section_idx["Parametri Kibana"] = i
            elif clean_line.startswith("3. Query Elasticsearch:"):
                section_idx["Query Elasticsearch"] = i

        if None in section_idx.values():
            raise ValueError("Le intestazioni '1.', '2.', '3.' non sono presenti nel formato previsto.")

        reasoning = "\n".join(lines[section_idx["Ragionamento"] + 1 : section_idx["Parametri Kibana"]]).strip()
        kibana_section = "\n".join(lines[section_idx["Parametri Kibana"] + 1 : section_idx["Query Elasticsearch"]]).strip()
        query_block = "\n".join(lines[section_idx["Query Elasticsearch"] + 1 :]).strip()

        from_date, to_date = "2025-02-28", "2025-03-24"
        filters = []
        current_field = None

        for line in kibana_section.splitlines():
            if line.strip().startswith("- Campo:"):
                current_field = line.split(":", 1)[1].strip()
            elif line.strip().startswith("- Valore:"):
                raw_value = line.split(":", 1)[1].strip()
                if current_field != "None" and raw_value != "None":
                    match = re.match(r"(>=|<=|>|<|=)?\s*(\d+)", raw_value)
                    if match:
                        op, val = match.groups()
                        filters.append((current_field, int(val), op or "="))
                    else:
                        filters.append((current_field, raw_value, "="))
            elif "Intervallo temporale" in line:
                parts = line.split("from")[1].split("to")
                from_date = parts[0].strip()
                to_date = parts[1].strip().split()[0]

        url = build_kibana_url(
            "http://localhost:5601",
            "4e177e0a-5007-407a-9a49-c936162be8a4",
            filters,
            from_date,
            to_date
        )

        st.markdown("### 🧠 Ragionamento del modello")
        st.markdown(f"<div style='background-color:#f5f5f5; padding:15px; border-radius:10px;'>{reasoning}</div>", unsafe_allow_html=True)

        st.markdown("### 🔧 Query Elasticsearch")
        st.code(query_block, language="json")

        st.markdown("### 🌐 URL Kibana")
        st.code(url, language="text")

        st.markdown("### 📊 Dashboard interattiva")
        st.markdown("""
        <div style='border: 1px solid #ccc; border-radius: 10px; overflow: hidden; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        st.components.v1.iframe(url, height=800, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Errore nell'elaborazione della risposta LLM: {e}")
        st.code(llm_output, language="markdown")
