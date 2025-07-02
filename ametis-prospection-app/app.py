import streamlit as st
import requests
from fpdf import FPDF
import tempfile
import time

# ======================================
# CONFIGURATION (avec fallback sécurisé)
# ======================================
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "Ametis2025")
except KeyError as e:
    st.error(f"Erreur de configuration : Clé secrète manquante ({e})")
    st.stop()

MODEL = "deepseek-chat"
API_URL = "https://api.deepseek.com/v1/chat/completions"

# ======================
# INITIALISATION DE L'APP
# ======================
def init_app():
    """Configure l'application et gère l'authentification"""
    st.set_page_config(
        page_title="Prospection Ametis",
        page_icon="🧐",
        layout="centered"
    )
    
    # Masquer les éléments Streamlit inutiles
    st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# =====================
# FONCTION PRINCIPALE
# =====================
def main_interface():
    """Interface principale de l'application"""
    # Vérification de l'authentification
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        with st.container(border=True):
            st.title("Authentification requise")
            password = st.text_input("Mot de passe :", type="password")
            
            if st.button("Se connecter"):
                if password == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Accès refusé")
        st.stop()
    
    # Interface principale après authentification
    st.title("🧐 Assistant Prospection Ametis")
    
    with st.form(key='prospection_form'):
        company = st.text_input("Nom de l'entreprise", placeholder="Ex: Actibio 53")
        sector = st.selectbox(
            "Secteur d'activité",
            ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", "Industrie", "Autre"]
        )
        
        if st.form_submit_button("Générer la fiche"):
            if company:
                with st.spinner("Analyse en cours..."):
                    headers = {
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    
                    data = {
                        "model": MODEL,
                        "messages": [{
                            "role": "user", 
                            "content": f"Génère une fiche de prospection pour {company} ({sector})"
                        }],
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }

                    try:
                        response = requests.post(API_URL, headers=headers, json=data, timeout=30)
                        if response.status_code == 200:
                            fiche = response.json()["choices"][0]["message"]["content"]
                            st.session_state.fiche = fiche
                            st.success("Fiche générée avec succès !")
                            st.markdown(fiche)
                        else:
                            st.error(f"Erreur API : {response.status_code} - {response.text}")
                    except Exception as e:
                        st.error(f"Erreur de connexion : {str(e)}")
            else:
                st.warning("Veuillez saisir un nom d'entreprise")

    # Export PDF
    if 'fiche' in st.session_state:
        if st.button("📄 Exporter en PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            for line in st.session_state.fiche.split('\n'):
                pdf.cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                pdf.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button(
                        "Télécharger la fiche",
                        data=f,
                        file_name=f"prospection_{company}.pdf",
                        mime="application/pdf"
                    )

# =============
# POINT D'ENTRÉE
# =============
if __name__ == "__main__":
    init_app()
    main_interface()
