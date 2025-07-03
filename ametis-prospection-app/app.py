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

# Configuration de la page Streamlit
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

# ----------------------------
# STYLE CSS
# ----------------------------

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
    
    .admin-dashboard {
        background-color: #fff4f4;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .loading-container {
        text-align: center;
        margin: 2rem 0;
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    @media (max-width: 640px) {
        .main-container {padding: 1rem;}
        .report-container {padding: 1rem;}
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# FONCTIONS UTILITAIRES
# ----------------------------

def load_history():
    """Charge l'historique des recherches depuis le fichier JSON"""
    try:
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'w') as f:
                json.dump([], f)
            return []
        
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
            return history if isinstance(history, list) else []
    except Exception as e:
        st.error(f"Erreur lors du chargement de l'historique: {str(e)}")
        return []

def save_history(history):
    """Sauvegarde l'historique des recherches dans le fichier JSON"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history[-MAX_HISTORY_ENTRIES:], f)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde de l'historique: {str(e)}")

def generate_pdf_report(data):
    """Génère un rapport PDF à partir des données de recherche"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(200, 10, txt="Rapport de Prospection Ametis", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Réalisé par: {st.session_state.current_user}", ln=1, align='C')
        
        pdf.ln(10)
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt=f"Entreprise: {data.get('entreprise', '')}", ln=1)
        
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=data.get('analyse', ''))
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF: {str(e)}")
        return None

# ----------------------------
# AUTHENTIFICATION
# ----------------------------

def authenticate():
    """Gère le processus d'authentification"""
    # Initialisation de la session
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.history = load_history()
    
    # Si non authentifié, afficher le formulaire de connexion
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

# ----------------------------
# INTERFACE PRINCIPALE
# ----------------------------

def main_app_interface():
    """Interface principale de l'application après authentification"""
    # Header
    st.title("😎 ASSISTANT Prospection Ametis")
    st.markdown(f"-VB1,1DS | Connecté en tant que: **{st.session_state.current_user}**")
    
    # Tableau de bord admin
    if st.session_state.current_user == "admin":
        with st.expander("🔧 TABLEAU DE BORD ADMIN", expanded=True):
            st.markdown("<div class='admin-dashboard'>", unsafe_allow_html=True)
            
            # Statistiques
            st.subheader("📊 Statistiques")
            total_searches = len(st.session_state.history)
            pro_searches = len([h for h in st.session_state.history if h.get('mode') == "PRO"])
            
            col1, col2 = st.columns(2)
            col1.metric("Total recherches", total_searches)
            col2.metric("Recherches PRO", pro_searches)
            
            # Dernières activités
            st.subheader("🕒 Activités récentes")
            if not st.session_state.history:
                st.write("Aucune activité enregistrée")
            else:
                for search in reversed(st.session_state.history[-5:]):
                    with st.container():
                        st.write(f"**{search.get('entreprise', 'N/A')}** ({search.get('date', 'N/A')})")
                        st.caption(f"Par {search.get('user', 'N/A')} | Mode: {search.get('mode', 'N/A')}")
            
            # Gestion des données
            st.subheader("🗃️ Gestion des données")
            if st.button("🗑️ Purger l'historique"):
                st.session_state.history = []
                save_history(st.session_state.history)
                st.success("Historique purgé avec succès")
                time.sleep(1)
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Formulaire de recherche
    with st.form("search_form"):
        st.subheader("🔍 Nouvelle recherche")
        
        col1, col2 = st.columns(2)
        with col1:
            nom_entreprise = st.text_input("Nom de l'entreprise", placeholder="Ex: Société XYZ")
            secteur_cible = st.selectbox("Secteur d'activité", [
                "Technologie", "Santé", "Finance", "Agroalimentaire"
                "Industrie", "Commerce", "Services"
            ])
        with col2:
            localisation = st.text_input("Localisation", placeholder="Ville ou région")
            recherche_pro = st.checkbox("Mode PRO (analyse approfondie)")
        
        submitted = st.form_submit_button("Lancer la recherche")
    
    # Traitement de la recherche
    if submitted:
        if not nom_entreprise:
            st.warning("Veuillez saisir un nom d'entreprise")
        else:
            with st.spinner("Analyse en cours..."):
                # Simulation d'une requête API
                try:
                    time.sleep(2)  # Simulation du temps de traitement
                    
                    # Génération de résultats fictifs pour l'exemple
                    analysis_result = {
                        "entreprise": nom_entreprise,
                        "secteur": secteur_cible,
                        "localisation": localisation,
                        "score": 85 if recherche_pro else 65,
                        "analyse": (
                            f"Analyse approfondie de {nom_entreprise} révèle un fort potentiel "
                            f"dans le secteur {secteur_cible}." if recherche_pro else
                            f"Analyse standard de {nom_entreprise} indique une opportunité "
                            f"modérée dans {secteur_cible}."
                        ),
                        "recommandations": [
                            "Prise de contact initiale par email",
                            "Proposition de rendez-vous téléphonique",
                            "Envoi de documentation ciblée"
                        ]
                    }
                    
                    # Affichage des résultats
                    with st.container():
                        st.subheader(f"📊 Résultats pour {nom_entreprise}")
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Score de potentiel", analysis_result["score"])
                        col2.metric("Secteur", analysis_result["secteur"])
                        
                        st.markdown("#### 🔍 Analyse")
                        st.write(analysis_result["analyse"])
                        
                        st.markdown("#### 📌 Recommandations")
                        for rec in analysis_result["recommandations"]:
                            st.write(f"- {rec}")
                        
                        # Bouton d'export PDF
                        pdf_data = {
                            "entreprise": nom_entreprise,
                            "analyse": analysis_result["analyse"],
                            "recommandations": "\n".join(analysis_result["recommandations"])
                        }
                        pdf_report = generate_pdf_report(pdf_data)
                        
                        st.download_button(
                            label="📄 Exporter en PDF",
                            data=pdf_report,
                            file_name=f"rapport_{nom_entreprise.lower().replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                    
                    # Mise à jour de l'historique
                    new_entry = {
                        'user': st.session_state.current_user,
                        'date': datetime.now(timezone(timedelta(hours=2))).strftime("%Y-%m-%d %H:%M:%S"),
                        'entreprise': nom_entreprise,
                        'mode': "PRO" if recherche_pro else "Standard",
                        'secteur': secteur_cible,
                        'tokens': 450 if recherche_pro else 250
                    }
                    
                    st.session_state.history.append(new_entry)
                    save_history(st.session_state.history)
                    st.success("Recherche enregistrée dans l'historique")
                
                except Exception as e:
                    st.error(f"Une erreur est survenue: {str(e)}")

# ----------------------------
# SIDEBAR
# ----------------------------

def app_sidebar():
    """Configure la sidebar de l'application"""
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
                filtered_history = [h for h in filtered_history if h.get('mode') == "PRO"]
            elif search_filter == "Standard":
                filtered_history = [h for h in filtered_history if h.get('mode') == "Standard"]
            elif search_filter == "Par utilisateur":
                filtered_history = [h for h in filtered_history if h.get('user') == st.session_state.current_user]
            
            for search in reversed(filtered_history[-10:]):
                with st.expander(f"{search.get('entreprise', 'N/A')} - {search.get('date', '').split()[0]}"):
                    st.write(f"**Utilisateur:** {search.get('user', 'N/A')}")
                    st.write(f"**Secteur:** {search.get('secteur', 'N/A')}")
                    st.write(f"**Mode:** {search.get('mode', 'N/A')}")
                    st.write(f"**Tokens utilisés:** {search.get('tokens', 'N/A')}")
        
        if st.button("🔒 Déconnexion"):
            st.session_state.clear()
            st.rerun()

# ----------------------------
# EXÉCUTION PRINCIPALE
# ----------------------------

def main():
    """Fonction principale de l'application"""
    authenticate()
    main_app_interface()
    app_sidebar()

if __name__ == "__main__":
    main()
