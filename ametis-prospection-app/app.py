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

# ----------------------------
# FONCTIONS CORE (inchangées)
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
# PROMPTS METIER (votre version exacte)
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
# INTERFACE (inchangée)
# ----------------------------

def authenticate():
    """Gère le processus d'authentification"""
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

def main_app_interface():
    """Interface principale de l'application"""
    st.title("🤖 ASSISTANT Prospection Ametis")
    st.markdown(f"-VB1,1DS | Connecté en tant que: **{st.session_state.current_user}**")
    
    # [Votre code existant pour le dashboard admin...]
    
    # Formulaire de recherche
    with st.form("search_form"):
        st.subheader("🔍 Nouvelle recherche")
        
        col1, col2 = st.columns(2)
        with col1:
            nom_entreprise = st.text_input("Nom de l'entreprise")
            secteur_cible = st.selectbox("Secteur d'activité", [
                "Technologie", "Santé", "Finance", "Industrie", "Commerce", "Services" , "Agroalimentaire"
            ])
        with col2:
            localisation = st.text_input("Localisation")
            recherche_pro = st.checkbox("Mode PRO (analyse approfondie)")
        
        submitted = st.form_submit_button("Lancer la recherche")
    
    # Traitement de la recherche
    if submitted:
        if not nom_entreprise:
            st.warning("Veuillez saisir un nom d'entreprise")
        else:
            with st.spinner("Analyse en cours..."):
                try:
                    # Génération du prompt adapté
                    prompt = generate_pro_prompt(nom_entreprise, secteur_cible, localisation) if recherche_pro else \
                             generate_standard_prompt(nom_entreprise, secteur_cible, localisation)
                    
                    # Simulation réponse API (à remplacer par votre implémentation réelle)
                    time.sleep(2)
                    
                    # Construction du résultat
                    analysis_result = {
                        "entreprise": nom_entreprise,
                        "contenu": f"""**Résultat simulé pour test**\n\n{prompt}"""
                    }
                    
                    # Affichage
                    st.subheader(f"📊 Résultats pour {nom_entreprise}")
                    st.markdown(analysis_result["contenu"])
                    
                    # Mise à jour historique
                    new_entry = {
                        'user': st.session_state.current_user,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'entreprise': nom_entreprise,
                        'mode': "PRO" if recherche_pro else "Standard",
                        'secteur': secteur_cible,
                        'tokens': len(prompt.split())  # Estimation
                    }
                    st.session_state.history.append(new_entry)
                    save_history(st.session_state.history)
                    
                    # Export PDF
                    pdf_report = generate_pdf_report({
                        "entreprise": nom_entreprise,
                        "analyse": analysis_result["contenu"]
                    })
                    st.download_button(
                        label="📄 Exporter en PDF",
                        data=pdf_report,
                        file_name=f"rapport_{nom_entreprise}.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")

def app_sidebar():
    """Configure la sidebar"""
    with st.sidebar:
        st.info(f"""
        **Session:** {st.session_state.current_user}
        **Version:** VBeta1,1DS
        **Dernière connexion:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """)
        
        st.markdown("---")
        st.subheader("📋 Historique complet")
        
        if st.session_state.history:
            for search in reversed(st.session_state.history[-5:]):
                st.caption(f"{search['entreprise']} ({search['date'].split()[0]})")
        
        if st.button("🔒 Déconnexion"):
            st.session_state.clear()
            st.rerun()

# ----------------------------
# EXECUTION
# ----------------------------

def main():
    authenticate()
    main_app_interface()
    app_sidebar()

if __name__ == "__main__":
    main()
