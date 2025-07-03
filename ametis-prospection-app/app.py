from dotenv import load_dotenv
import streamlit as st
import requests
import os
import time
import json
from datetime import datetime, timezone, timedelta
from fpdf import FPDF

# Configuration initiale
HISTORY_FILE = "search_history.json"
USER_CREDENTIALS = {
    "admin": os.getenv("ADMIN_PASSWORD", "admin"),
    "NPI": os.getenv("COMMERCIAL1_PWD", "Ametis2025"),
    "commercial2": os.getenv("COMMERCIAL2_PWD", "Commercial456")
}

# Configuration de la page
st.set_page_config(
    page_title="Assistant Prospection Ametis VBeta V1,1DS",
    layout="centered",
    page_icon="🤖",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Style CSS avec animation
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main-container {
        max-width: 900px;
        padding: 2rem;
        margin: 0 auto;
    }
    .report-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 2rem;
        margin-top: 1rem;
        word-wrap: break-word;
    }
    
    /* Animation de chargement */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .loading-container {
        text-align: center;
        margin: 2rem 0;
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f2f6;
    }
    
    .admin-dashboard {
        background-color: #fff4f4;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    @media (max-width: 640px) {
        .main-container {padding: 1rem;}
        .report-container {padding: 1rem;}
    }
</style>
""", unsafe_allow_html=True)

# Gestion des données
def load_history():
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-100:], f)  # Garde seulement les 100 dernières entrées

# Authentification
def authenticate():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.history = load_history()

    if not st.session_state.authenticated:
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("👤 Identifiant")
        with col2:
            password = st.text_input("🔒 Mot de passe", type="password")
        
        if st.button("Se connecter"):
            if USER_CREDENTIALS.get(username) == password:
                st.session_state.authenticated = True
                st.session_state.current_user = username
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect")
        st.stop()

authenticate()

# Header
st.title(f"🫣 ASSISTANT Prospection Ametis")
st.markdown(f"-VB1,1DS | Connecté en tant que: **{st.session_state.current_user}**")

# Tableau de bord admin
if st.session_state.current_user == "admin":
    with st.expander("🔧 TABLEAU DE BORD ADMIN", expanded=True):
        st.markdown("<div class='admin-dashboard'>", unsafe_allow_html=True)
        
        # Statistiques
        st.subheader("📊 Statistiques")
        total_searches = len(st.session_state.history)
        pro_searches = len([h for h in st.session_state.history if h['mode'] == "PRO"])
        
        col1, col2 = st.columns(2)
        col1.metric("Total recherches", total_searches)
        col2.metric("Recherches PRO", pro_searches)
        
        # Dernières activités
        st.subheader("🕒 Activités récentes")
        if not st.session_state.history:
            st.write("Aucune activité enregistrée")
        else:
            for i, search in enumerate(reversed(st.session_state.history[-5:])):
                st.write(f"**{search['entreprise']}** ({search['date']})")
                st.caption(f"Par {search['user']} | Mode: {search['mode']} | Tokens: {search['tokens']}")
        
        # Gestion des données
        st.subheader("🗃️ Gestion des données")
        if st.button("🗑️ Purger l'historique"):
            st.session_state.history = []
            save_history(st.session_state.history)
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)

# ... [Le reste de votre code existant (paramètres, formulaire, etc.) reste inchangé jusqu'au traitement de la recherche] ...

# Dans la partie traitement de la recherche (après avoir obtenu la réponse API)
if response.status_code == 200:
    # ... [code existant] ...
    
    # Mise à jour de l'historique
    new_entry = {
        'user': st.session_state.current_user,
        'date': datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d %H:%M:%S"),
        'entreprise': nom_entreprise,
        'mode': "PRO" if recherche_pro else "Standard",
        'tokens': tokens_used,
        'secteur': secteur_cible
    }
    
    st.session_state.history.append(new_entry)
    save_history(st.session_state.history)

# ... [Le reste de votre code existant (affichage résultats, export PDF) reste inchangé] ...

# Sidebar modifiée
with st.sidebar:
    st.info(f"""
    **Session:** {st.session_state.current_user}
    **Version:** VB1,1DS
    **Dernière connexion:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """)
    
    st.markdown("---")
    st.subheader("📋 Historique complet")
    
    if not st.session_state.history:
        st.write("Aucune recherche enregistrée")
    else:
        search_filter = st.selectbox("Filtrer par:", ["Tous", "PRO", "Standard", "Par utilisateur"])
        
        filtered_history = st.session_state.history.copy()
        if search_filter == "PRO":
            filtered_history = [h for h in filtered_history if h['mode'] == "PRO"]
        elif search_filter == "Standard":
            filtered_history = [h for h in filtered_history if h['mode'] == "Standard"]
        elif search_filter == "Par utilisateur":
            filtered_history = [h for h in filtered_history if h['user'] == st.session_state.current_user]
        
        for search in reversed(filtered_history[-10:]):  # Affiche les 10 dernières
            with st.expander(f"{search['entreprise']} - {search['date'].split()[0]}"):
                st.write(f"**Utilisateur:** {search['user']}")
                st.write(f"**Secteur:** {search['secteur']}")
                st.write(f"**Mode:** {search['mode']}")
                st.write(f"**Tokens utilisés:** {search['tokens']}")
    
    if st.button("🔒 Déconnexion"):
        st.session_state.clear()
        st.rerun()
