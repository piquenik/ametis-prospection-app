import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone, timedelta
from fpdf import FPDF
import time

# ----------------------------
# CONFIGURATION AMÉLIORÉE POUR MODE R1
# ----------------------------

def call_deepseek_api(prompt: str, recherche_pro: bool = False, mode_r1: bool = False) -> str:
    """Appel API optimisé pour les modes R1 et DeepSeek"""
    headers = {
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    # Configuration spécifique pour le mode R1
    if mode_r1:
        payload = {
            "model": "deepseek-r1",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.5,  # Plus conservateur pour R1
            "max_tokens": 1500,
            "top_p": 0.9
        }
    else:
        # Configuration standard
        payload = {
            "model": "deepseek-pro" if recherche_pro else "deepseek-chat",
            "messages": [{
                "role": "user",
                "content": prompt
            }],
            "temperature": 0.7,
            "max_tokens": 2000
        }
    
    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=45  # Timeout augmenté pour R1
        )
        
        # Vérification spécifique des erreurs R1
        if response.status_code == 400 and mode_r1:
            error_msg = response.json().get('error', {}).get('message', '')
            if "unsupported model" in error_msg.lower():
                raise ValueError("Le modèle R1 n'est pas disponible sur votre abonnement API")
        
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Erreur API ({'R1' if mode_r1 else 'Standard'}): "
        if isinstance(e, requests.exceptions.HTTPError):
            error_msg += f"HTTP {response.status_code}"
            if response.status_code == 400:
                error_msg += " - Requête invalide (vérifiez vos paramètres)"
            elif response.status_code == 429:
                error_msg += " - Quota dépassé"
        else:
            error_msg += str(e)
        st.error(error_msg)
        return None

# ----------------------------
# INTERFACE AVEC MODE R1
# ----------------------------

def main_app_interface():
    """Interface avec gestion spécifique du mode R1"""
    st.title("🤖 ASSISTANT Prospection Ametis")
    
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        with col1:
            nom_entreprise = st.text_input("Nom de l'entreprise*")
            secteur_cible = st.selectbox("Secteur d'activité*", ["Agroalimentaire", "Technologie", "Santé"])
        with col2:
            localisation = st.text_input("Localisation*")
            recherche_pro = st.checkbox("Mode PRO (analyse approfondie)")
            mode_r1 = st.checkbox("Activer la recherche R1")
        
        submitted = st.form_submit_button("Lancer la recherche")
    
    if submitted:
        if not all([nom_entreprise, secteur_cible, localisation]):
            st.warning("Veuillez remplir tous les champs obligatoires")
            return
            
        with st.spinner(f"🔍 Analyse en cours ({'R1' if mode_r1 else 'PRO' if recherche_pro else 'Standard'})..."):
            try:
                prompt = generate_pro_prompt(nom_entreprise, secteur_cible, localisation) if recherche_pro \
                         else generate_standard_prompt(nom_entreprise, secteur_cible, localisation)
                
                api_response = call_deepseek_api(prompt, recherche_pro, mode_r1)
                
                if api_response:
                    display_results(api_response)
                    
            except Exception as e:
                st.error(f"Erreur spécifique au mode R1: {str(e)}")
                st.info("Conseil: Désactivez le mode R1 ou vérifiez votre abonnement API")

# ----------------------------
# FONCTIONS EXISTANTES (inchangées)
# ----------------------------

def generate_standard_prompt(entreprise, secteur, localisation):
    return f"""Génère une fiche entreprise structurée pour :
- Entreprise: {entreprise}
- Secteur: {secteur}
- Localisation: {localisation}

### Structure requise:
1. **Résumé** (secteur + localisation)
2. **Activité** (description courte)
3. **Chiffres** (CA, effectifs, sites)
4. **Actualité** (2-3 événements récents)
5. **Contacts** (noms vérifiés uniquement)

Format Markdown strict."""

def generate_pro_prompt(entreprise, secteur, localisation):
    return f"""Génère une analyse approfondie pour :
- Entreprise: {entreprise}
- Secteur: {secteur}
- Localisation: {localisation}

### Structure requise:
1. **Analyse Stratégique** (positionnement concurrentiel)
2. **Potentiel Commercial** (opportunités Ametis)
3. **Décideurs Clés** (noms + postes vérifiés)
4. **Recommandations** (approche personnalisée)
5. **Risques** (éléments à considérer)

Format Markdown strict avec emojis pour hiérarchiser l'information."""

# ... [le reste de votre code existant] ...

if __name__ == "__main__":
    main()
