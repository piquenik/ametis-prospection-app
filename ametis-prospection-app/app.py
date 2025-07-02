import streamlit as st
import requests
from fpdf import FPDF
import tempfile
import time

# Configuration sécurisée
DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
MODEL = "deepseek-chat"  # Modèle à utiliser
API_URL = "https://api.deepseek.com/v1/chat/completions"

# ======================
# CONFIGURATION DE L'APP
# ======================
def setup_page():
    """Configure l'interface de l'application"""
    st.set_page_config(
        page_title="Prospection Ametis",
        page_icon="🧐",
        layout="centered"
    )
    
    # Masquer les éléments Streamlit inutiles
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stToolbar"] {display: none;}
    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =================
# AUTHENTIFICATION
# =================
def check_auth():
    """Gère l'authentification par mot de passe"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        with st.container(border=True):
            st.title("Accès sécurisé")
            password = st.text_input("Entrez le mot de passe :", type="password")
            
            if st.button("Valider"):
                if password == st.secrets.get("APP_PASSWORD", "Ametis2025"):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        st.stop()

# =====================
# FONCTION PRINCIPALE
# =====================
def generate_prospection_file(company, sector):
    """Génère la fiche de prospection via l'API DeepSeek"""
    prompt = f"""
    Tu es un expert en prospection B2B pour Ametis. Génère une fiche détaillée pour {company} ({sector}) contenant :
    1. 🏢 Coordonnées complètes (adresse, site web, logo)
    2. 📌 Activité principale et positionnement marché
    3. 🔍 Contacts clés (Production, Qualité, Achats)
    4. ✉️ Email de prospection personnalisé
    5. 📊 Analyse stratégique (criticité, budget estimé)
    6. 🗺️ Entreprises similaires dans un rayon de 50km
    
    Sois concis mais complet. Les données doivent être exploitables directement.
    """
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Erreur lors de la génération : {str(e)}")
        return None

# ================
# EXPORT EN PDF
# ================
def create_pdf(content, filename):
    """Crée un PDF à partir du contenu généré"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for line in content.split('\n'):
        pdf.cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        pdf.output(tmp.name)
        return tmp.name

# ==============
# INTERFACE UI
# ==============
def main_interface():
    """Affiche l'interface principale"""
    st.title("🧐 Assistant Prospection Ametis")
    st.markdown("""
    **Générez des fiches de prospection complètes**  
    *Entrez le nom d'une entreprise et sélectionnez son secteur d'activité*
    """)
    
    with st.form(key='prospection_form'):
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Nom de l'entreprise", placeholder="Ex: Actibio 53")
        with col2:
            sector = st.selectbox(
                "Secteur d'activité",
                ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", "Industrie", "Autre"]
            )
        
        if st.form_submit_button("Générer la fiche", type="primary"):
            if company:
                with st.spinner("Analyse en cours..."):
                    start_time = time.time()
                    report = generate_prospection_file(company, sector)
                    
                    if report:
                        st.session_state.report = report
                        st.success(f"Analyse complétée en {time.time()-start_time:.1f}s")
                        st.divider()
                        st.markdown(report)
            else:
                st.warning("Veuillez saisir un nom d'entreprise")

    if 'report' in st.session_state:
        pdf_file = create_pdf(st.session_state.report, f"prospection_{company}.pdf")
        with open(pdf_file, "rb") as f:
            st.download_button(
                "📄 Télécharger la fiche PDF",
                data=f,
                file_name=f"prospection_{company}.pdf",
                mime="application/pdf"
            )

# =============
# POINT D'ENTRÉE
# =============
if __name__ == "__main__":
    setup_page()
    check_auth()
    main_interface()
