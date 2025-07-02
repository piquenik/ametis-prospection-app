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
    
    # Gestion de l'authentification
    if not st.session_state.get('authenticated'):
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

# ... (le reste du code main_interface() et fonctions précédentes reste identique)

if __name__ == "__main__":
    init_app()
    main_interface()
