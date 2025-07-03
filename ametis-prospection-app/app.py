import streamlit as st
import requests
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timezone, timedelta
from fpdf import FPDF
import time
import logging

# ----------------------------
# CONFIGURATION INITIALE
# ----------------------------

# Constantes
HISTORY_FILE = "search_history.json"
MAX_HISTORY_ENTRIES = 100
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_TIMEOUT_CONNECT = 10  # Timeout de connexion en secondes
API_TIMEOUT_READ = 30     # Timeout de lecture en secondes

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv('USER_CREDENTIALS.env')

# Configuration des identifiants
USER_CREDENTIALS = {
    "admin": os.getenv("ADMIN", "admin"),
    "NPI": os.getenv("NPI", "Ametis2025"),
    "OB0": os.getenv("OB0", "Ametis2025"),
    "NDS": os.getenv("NDS", "Ametis2025"),
    "GBE": os.getenv("GBE", "Ametis2025"),
    "SSZ": os.getenv("SSZ", "Ametis2025"),
    "WVA": os.getenv("WVA", "Ametis2025"),
    "PMO": os.getenv("PMO", "Ametis2025"),
    "JNB": os.getenv("JNB", "Ametis2025"),
    "LCA": os.getenv("LCA", "Ametis2025"),
    "SNA": os.getenv("SNA", "Ametis2025"),
    "YCB": os.getenv("YCB", "Ametis2025")
}

# ----------------------------
# FONCTIONS UTILITAIRES
# ----------------------------

def load_history():
    """Charge l'historique des recherches depuis le fichier JSON"""
    try:
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
            return []
        
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur historique: {str(e)}")
        st.error("Erreur lors du chargement de l'historique")
        return []

def save_history(history):
    """Sauvegarde l'historique des recherches"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history[-MAX_HISTORY_ENTRIES:], f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Erreur sauvegarde: {str(e)}")
        st.error("Erreur lors de la sauvegarde de l'historique")

def generate_pdf_report(data):
    """Génère un rapport PDF avec police standard"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(200, 10, txt="Rapport de Prospection Ametis", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Date: {datetime.now(french_tz).strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
        
        clean_text = data.get('analyse', '').replace('€', 'EUR').replace('\u20ac', 'EUR')
        pdf.multi_cell(0, 10, txt=clean_text)
        
        return pdf.output(dest='S').encode('latin-1', 'replace')
    except Exception as e:
        logger.error(f"Erreur PDF: {str(e)}")
        st.error("Erreur lors de la génération du PDF")
        return None

def call_deepseek_api(prompt: str, reasoner: bool = False) -> str:
    """Appel robuste à l'API DeepSeek avec gestion des erreurs"""
    headers = {
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat" if not pro_mode else "deepseek-pro",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0
    }
    
    try:
        logger.info(f"Envoi requête à l'API DeepSeek (mode {'PRO' if pro_mode else 'Standard'})")
        start_time = time.time()
        
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=(API_TIMEOUT_CONNECT, API_TIMEOUT_READ)
        )
        
        response_time = time.time() - start_time
        logger.info(f"Réponse reçue en {response_time:.2f}s - Status: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', 'Requête invalide')
            logger.error(f"Erreur 400: {error_msg}")
            st.error(f"Erreur de validation : {error_msg}")
            return None
        
        response.raise_for_status()
        
        response_data = response.json()
        if not isinstance(response_data.get('choices'), list):
            logger.error("Format de réponse inattendu")
            st.error("Erreur: Format de réponse API inattendu")
            return None
            
        return response_data["choices"][0]["message"]["content"]
        
    except requests.exceptions.Timeout:
        logger.error("Timeout lors de l'appel API")
        st.error("Délai d'attente dépassé - Le serveur n'a pas répondu")
        st.info("Veuillez réessayer ou vérifier votre connexion Internet")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau: {str(e)}")
        st.error("Erreur de connexion avec l'API DeepSeek")
        return None
        
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        st.error("Une erreur inattendue est survenue")
        return None

# ----------------------------
# PROMPTS METIER (inchangés)
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

# ----------------------------
# INTERFACE UTILISATEUR (inchangée)
# ----------------------------

def authenticate():
    """Gère l'authentification"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.history = load_history()
    
    if not st.session_state.authenticated:
        st.title("🔐 Connexion à l'Assistant Prospection")
        
        with st.form("auth_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("👤 Identifiant")
            with col2:
                password = st.text_input("🔒 Mot de passe", type="password")
            
            if st.form_submit_button("Se connecter"):
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect")
        st.stop()

def display_results_container(content):
    """Affiche les résultats dans un conteneur responsive"""
    st.markdown(f"""
    <div style="
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-top: 20px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
    ">
        <div style="max-width: 100%; overflow-x: auto;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def main_app_interface():
    """Interface principale"""
    st.title("🤖 ASSISTANT Prospection Ametis")
    st.markdown(f"-VB1,1DS | Connecté en tant que: **{st.session_state.current_user}**")
    
    with st.form("search_form"):
        st.subheader("🔍 Nouvelle recherche")
        
        col1, col2 = st.columns(2)
        with col1:
            nom_entreprise = st.text_input("Nom de l'entreprise*", placeholder="Ex: Société XYZ")
            secteur_cible = st.selectbox("Secteur d'activité*", [
                "Agroalimentaire", "Technologie", "Santé", "Finance", "Industrie", "Commerce", "Services"
            ])
        with col2:
            localisation = st.text_input("Localisation*", placeholder="Ville ou région")
            recherche_pro = st.checkbox("Mode PRO (analyse approfondie)")
        
        submitted = st.form_submit_button("Lancer la recherche")
        st.caption("*Champs obligatoires - Les données sont estimées si non publiques")
    
    if submitted:
        if not nom_entreprise or not localisation:
            st.warning("Veuillez remplir tous les champs obligatoires")
        else:
            with st.spinner("🔍 Analyse en cours avec DeepSeek..."):
                try:
                    prompt = generate_pro_prompt(nom_entreprise, secteur_cible, localisation) if recherche_pro \
                             else generate_standard_prompt(nom_entreprise, secteur_cible, localisation)
                    
                    api_response = call_deepseek_api(prompt, recherche_pro)
                    
                    if api_response:
                        st.success("Analyse complétée avec succès")
                        st.subheader(f"📊 Résultats pour {nom_entreprise}")
                        display_results_container(api_response)
                        
                        new_entry = {
                            'user': st.session_state.current_user,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'entreprise': nom_entreprise,
                            'mode': "PRO" if recherche_pro else "Standard",
                            'secteur': secteur_cible,
                            'tokens': len(prompt.split())
                        }
                        st.session_state.history.append(new_entry)
                        save_history(st.session_state.history)
                        
                        pdf_report = generate_pdf_report({
                            'entreprise': nom_entreprise,
                            'analyse': api_response
                        })
                        
                        if pdf_report:
                            st.download_button(
                                label="📄 Exporter en PDF",
                                data=pdf_report,
                                file_name=f"rapport_{nom_entreprise}.pdf",
                                mime="application/pdf"
                            )
                    
                except Exception as e:
                    logger.error(f"Erreur traitement: {str(e)}")
                    st.error("Une erreur est survenue lors du traitement")

def app_sidebar():
    """Configure la sidebar"""
    with st.sidebar:
        st.info(f"""
        **Session:** {st.session_state.current_user}
        **Version:** VB1,1DS
        **Dernière activité:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """)
        
        st.markdown("---")
        st.subheader("📋 Historique complet")
        
        if not st.session_state.history:
            st.write("Aucune recherche enregistrée")
        else:
            for search in reversed(st.session_state.history[-5:]):
                st.caption(f"{search['entreprise']} ({search['date'].split()[0]}) - {search['mode']}")
        
        if st.button("🔒 Déconnexion"):
            st.session_state.clear()
            st.rerun()

# ----------------------------
# FONCTION PRINCIPALE
# ----------------------------

def main():
    """Point d'entrée principal"""
    st.set_page_config(
        page_title="Assistant Prospection Ametis",
        layout="centered",
        page_icon="🤖",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    authenticate()
    main_app_interface()
    app_sidebar()

if __name__ == "__main__":
    main()
