import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration robuste des requêtes API
def setup_api_session():
    session = requests.Session()
    retries = Retry(
        total=3,  # Nombre total de tentatives
        backoff_factor=1,  # Délai entre les tentatives (1, 2, 4 sec)
        status_forcelist=[408, 429, 500, 502, 503, 504]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

# Fonction de génération avec gestion d'erreur améliorée
def generate_prospection(company, sector):
    api_session = setup_api_session()
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{
            "role": "user",
            "content": f"Génère une fiche de prospection pour {company} ({sector})"
        }],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    headers = {
        "Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}",
        "Content-Type": "application/json"
    }

    try:
        with st.spinner("Analyse en cours (peut prendre 30 secondes)..."):
            response = api_session.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45  # Timeout augmenté à 45 secondes
            )
            
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"Erreur API (HTTP {response.status_code}): {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("""**Temps d'attente dépassé** - Solutions :
        - Réessayez dans 1 minute
        - Vérifiez votre connexion Internet
        - Contactez le support si le problème persiste
        """)
        return None
    except Exception as e:
        st.error(f"Erreur inattendue : {str(e)}")
        return None
