import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fpdf import FPDF
import tempfile

# Configuration
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "Ametis2025")
except KeyError as e:
    st.error(f"Erreur de configuration : {e}")
    st.stop()

# Initialisation
st.set_page_config(page_title="Prospection Ametis", layout="centered")
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Gestion API (version robuste)
def call_deepseek(prompt):
    session = requests.Session()
    adapter = HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
    )
    session.mount("https://", adapter)
    
    try:
        response = session.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2000
            },
            timeout=30
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Erreur API : {str(e)[:100]}...")  # Limite la taille du message
        return None

# Interface
def main():
    # Authentification
    if not st.session_state.get('auth'):
        with st.container():
            st.title("Authentification")
            if st.text_input("Mot de passe", type="password") == APP_PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.stop()
    
    # Application principale
    st.title("🧐 Prospection Ametis")
    company = st.text_input("Nom de l'entreprise")
    sector = st.selectbox("Secteur", ["Agroalimentaire", "Industrie"])
    
    if st.button("Générer"):
        if company:
            with st.spinner("Génération en cours..."):
                fiche = call_deepseek(f"Génère une fiche prospection pour {company} ({sector})")
                if fiche:
                    st.session_state.fiche = fiche
                    st.markdown(fiche)
        else:
            st.warning("Nom d'entreprise requis")

    # Export PDF
    if st.session_state.get('fiche'):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in st.session_state.fiche.split('\n'):
            pdf.cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button(
                    "📄 Télécharger PDF",
                    data=f.read(),
                    file_name=f"fiche_{company}.pdf",
                    mime="application/pdf"
                )

if __name__ == "__main__":
    main()
