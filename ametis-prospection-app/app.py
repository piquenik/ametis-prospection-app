import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone, timedelta
from fpdf import FPDF
import time

# ----------------------------
# CONFIGURATION INITIALE
# ----------------------------

# Constantes
HISTORY_FILE = "search_history.json"
MAX_HISTORY_ENTRIES = 100
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Chargement des variables d'environnement
load_dotenv('USER_CREDENTIALS.env')

# Configuration des identifiants
USER_CREDENTIALS = {
    "admin": os.getenv("ADMIN", "admin"),
    "NPI": os.getenv("NPI", "Ametis2025"),
    # ... (autres identifiants)
}

# ----------------------------
# FONCTIONS CORE - CORRECTION API
# ----------------------------

def call_deepseek_api(prompt: str, pro_mode: bool = False) -> str:
    """Appel sécurisé à l'API DeepSeek avec meilleure gestion des erreurs"""
    headers = {
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat" if not pro_mode else "deepseek-pro",
        "messages": [{
            "role": "user",
            "content": prompt
        }],
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Analyse détaillée de la réponse
        if response.status_code == 400:
            error_detail = response.json().get('error', {}).get('message', 'Requête mal formée')
            raise ValueError(f"Erreur de validation API: {error_detail}")
        elif response.status_code == 401:
            raise ValueError("Clé API non autorisée ou invalide")
        elif response.status_code == 429:
            raise ValueError("Quota API dépassé")
        elif response.status_code >= 500:
            raise ValueError("Erreur serveur DeepSeek")
        
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
        
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur réseau: {str(e)}")
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"Erreur inattendue: {str(e)}")
    
    return None

# ----------------------------
# INTERFACE - VALIDATION AMELIOREE
# ----------------------------

def main_app_interface():
    """Interface principale avec validation améliorée"""
    st.title("🤖 ASSISTANT Prospection Ametis")
    st.markdown(f"-VB1,1DS | Connecté en tant que: **{st.session_state.current_user}**")
    
    # Formulaire de recherche avec validation
    with st.form("search_form", clear_on_submit=False):
        st.subheader("🔍 Nouvelle recherche")
        
        col1, col2 = st.columns(2)
        with col1:
            nom_entreprise = st.text_input(
                "Nom de l'entreprise*",
                placeholder="Ex: Société XYZ",
                max_chars=100
            )
            secteur_cible = st.selectbox(
                "Secteur d'activité*",
                ["Agroalimentaire", "Technologie", "Santé", "Finance", "Industrie", "Commerce", "Services"]
            )
        with col2:
            localisation = st.text_input(
                "Localisation*",
                placeholder="Ville ou région",
                max_chars=50
            )
            recherche_pro = st.checkbox("Mode PRO (analyse approfondie)")
        
        submitted = st.form_submit_button("Lancer la recherche")
        st.caption("*Champs obligatoires - Les données sont estimées si non publiques")
    
    # Traitement de la recherche avec validation renforcée
    if submitted:
        # Validation des entrées
        if not nom_entreprise or not localisation:
            st.warning("Veuillez remplir tous les champs obligatoires")
            return
        
        if len(nom_entreprise) < 2:
            st.warning("Le nom de l'entreprise doit contenir au moins 2 caractères")
            return
        
        with st.spinner("🔍 Analyse en cours avec DeepSeek..."):
            try:
                # Génération du prompt avec validation
                prompt = generate_pro_prompt(nom_entreprise, secteur_cible, localisation) if recherche_pro \
                         else generate_standard_prompt(nom_entreprise, secteur_cible, localisation)
                
                if not prompt or len(prompt) < 20:
                    st.error("Erreur de génération du prompt")
                    return
                
                # Appel API avec gestion des erreurs
                start_time = time.time()
                api_response = call_deepseek_api(prompt, recherche_pro)
                
                if not api_response:
                    st.error("L'API n'a pas retourné de réponse valide")
                    return
                
                processing_time = time.time() - start_time
                
                # Affichage des résultats
                st.success(f"Analyse complétée en {processing_time:.2f}s")
                display_results(api_response, nom_entreprise, recherche_pro, secteur_cible)
                
            except Exception as e:
                st.error(f"Erreur lors du traitement: {str(e)}")
                st.info("Veuillez vérifier vos informations et réessayer")

# ... [le reste de votre code existant inchangé] ...

if __name__ == "__main__":
    main()
