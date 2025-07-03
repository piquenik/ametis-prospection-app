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

# ----------------------------
# FONCTIONS CORE
# ----------------------------

def load_history():
    """Charge l'historique des recherches depuis le fichier JSON"""
    try:
        if not os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'w') as f:
                json.dump([], f)
            return []
        
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erreur historique: {str(e)}")
        return []

def save_history(history):
    """Sauvegarde l'historique des recherches"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history[-MAX_HISTORY_ENTRIES:], f)
    except Exception as e:
        st.error(f"Erreur sauvegarde: {str(e)}")

def generate_pdf_report(data):
    """Génère un rapport PDF"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Rapport de Prospection", ln=1, align='C')
        pdf.multi_cell(0, 10, txt=data.get('analyse', ''))
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Erreur PDF: {str(e)}")
        return None

def call_deepseek_api(prompt: str, pro_mode: bool = False) -> str:
    """Appel réel à l'API DeepSeek"""
    headers = {
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat" if not pro_mode else "deepseek-pro",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Erreur API DeepSeek: {str(e)}")
        return None

# ----------------------------
# PROMPTS METIER
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
# FONCTIONS D'INTERFACE
# ----------------------------

def authenticate():
    """Gère l'authentification"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.history = load_history()
    
    if not st.session_state.authenticated:
        st.title("🔐 Connexion")
        username = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type="password")
        
        if st.button("Se connecter"):
            if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                st.session_state.authenticated = True
                st.session_state.current_user = username
                st.rerun()
            else:
                st.error("Identifiants incorrects")
        st.stop()

def app_sidebar():
    """Configure la sidebar"""
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
            for search in reversed(st.session_state.history[-5:]):
                st.caption(f"{search['entreprise']} ({search['date'].split()[0]})")
        
        if st.button("🔒 Déconnexion"):
            st.session_state.clear()
            st.rerun()

def main_app_interface():
    """Interface principale avec intégration réelle de DeepSeek"""
    st.title("🤖 ASSISTANT Prospection Ametis")
    st.markdown(f"-VB1,1DS | Connecté en tant que: **{st.session_state.current_user}**")
    
    # Formulaire de recherche
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
        st.caption("*Champs obligatoires")
    
    # Traitement de la recherche
    if submitted:
        if not nom_entreprise or not localisation:
            st.warning("Veuillez remplir tous les champs obligatoires")
        else:
            with st.spinner("🔍 Analyse en cours avec DeepSeek..."):
                try:
                    # Génération du prompt adapté
                    prompt = generate_pro_prompt(nom_entreprise, secteur_cible, localisation) if recherche_pro else \
                             generate_standard_prompt(nom_entreprise, secteur_cible, localisation)
                    
                    # Appel réel à l'API DeepSeek
                    start_time = time.time()
                    api_response = call_deepseek_api(prompt, recherche_pro)
                    
                    if api_response:
                        processing_time = time.time() - start_time
                        
                        # Affichage des résultats
                        st.success(f"Analyse complétée en {processing_time:.2f}s")
                        st.subheader(f"📊 Résultats pour {nom_entreprise}")
                        st.markdown(api_response, unsafe_allow_html=True)
                        
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
                            "analyse": api_response
                        })
                        
                        st.download_button(
                            label="📄 Exporter en PDF",
                            data=pdf_report,
                            file_name=f"rapport_prospection_{nom_entreprise}.pdf",
                            mime="application/pdf"
                        )
                    
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse: {str(e)}")

# ----------------------------
# FONCTION PRINCIPALE
# ----------------------------

def main():
    """Point d'entrée principal"""
    # Chargement des variables d'environnement
    load_dotenv('USER_CREDENTIALS.env')
    
    # Configuration des identifiants
    global USER_CREDENTIALS
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
    
    # Flux d'exécution
    authenticate()
    main_app_interface()
    app_sidebar()

# ----------------------------
# POINT D'ENTRÉE
# ----------------------------

if __name__ == "__main__":
    main()
