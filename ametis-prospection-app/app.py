import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ... (conservez tout le code existant jusqu'à la partie API)

# =====================
# PARTIE MODIFIÉE (uniquement la gestion de l'API)
# =====================
def call_deepseek_api(prompt_content):
    """Fonction modifiée avec meilleure gestion du timeout"""
    session = requests.Session()
    
    # Configuration des retry et timeout
    retry_strategy = Retry(
        total=3,  # 3 tentatives
        backoff_factor=1,  # Délai entre les retries (1s, 2s, 4s)
        status_forcelist=[408, 429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    
    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt_content}],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        response = session.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=45  # Timeout augmenté à 45 secondes
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
        
    except requests.exceptions.Timeout:
        st.error("L'API met trop de temps à répondre. Veuillez réessayer.")
        return None
    except Exception as e:
        st.error(f"Erreur API: {str(e)}")
        return None

# ... (conservez le reste de votre code existant)

# Dans votre fonction de génération, remplacez simplement l'appel API par:
# result = call_deepseek_api(votre_prompt)
