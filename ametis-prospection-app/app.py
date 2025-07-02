import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile

# Configuration
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "Ametis2025")
except:
    st.error("Erreur de configuration")
    st.stop()

# Initialisation
st.set_page_config(page_title="Prospection Ametis", layout="centered")
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Nouvel endpoint API
API_URL = "https://api.deepseek.ai/v1/chat/completions"  # <--- CHANGEMENT IMPORTANT ICI

# Fonction API robuste
def call_deepseek_api(prompt, max_retries=2):
    """Fonction optimisée pour la nouvelle URL d'API"""
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = requests.post(
                API_URL,  # Utilisation du nouvel endpoint
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1500
                },
                timeout=(5, 35)  # Connect: 5s, Read: 35s
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                st.warning(f"Tentative {attempt+1} échouée (HTTP {response.status_code})")
                
        except requests.exceptions.Timeout:
            st.warning(f"Tentative {attempt+1} : Timeout - Réessai...")
            time.sleep(1.5)  # Pause légèrement plus longue
            
        except Exception as e:
            st.error(f"Erreur : {str(e)[:100]}")
            return None
    
    return None  # Toutes les tentatives ont échoué

# Solution de repli locale (conservée)
def generate_fallback_report(company, sector):
    return f"""
# Fiche Prospection: {company}

**Secteur:** {sector}

## Coordonnées
- Adresse: Non disponible (erreur API)
- Site web: www.{company.replace(' ', '').lower()}.fr
- Téléphone: 01 23 45 67 89

## Activité
Description générée localement - L'API DeepSeek n'a pas répondu.

## Contacts clés
- Responsable production: contact@{company.replace(' ', '').lower()}.fr
- Responsable qualité: qualite@{company.replace(' ', '').lower()}.fr

## Stratégie d'approche
Privilégier un contact par email avec proposition de démonstration gratuite.
"""

# Interface principale
def main():
    # Authentification
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        with st.container():
            st.title("🔒 Authentification")
            password = st.text_input("Mot de passe", type="password")
            if st.button("Valider"):
                if password == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Accès refusé")
            st.stop()
    
    # Application principale
    st.title("🧐 Prospection Ametis")
    company = st.text_input("Nom de l'entreprise", "ACTIBIO 53")
    sector = st.selectbox("Secteur", ["Agroalimentaire", "Industrie", "Logistique", "Autre"], index=0)
    
    if st.button("Générer la fiche", type="primary"):
        if not company:
            st.warning("Veuillez saisir un nom d'entreprise")
            return
            
        with st.spinner("Génération en cours..."):
            # Tentative API avec le nouvel endpoint
            prompt = f"Génère une fiche de prospection détaillée pour {company} dans le secteur {sector}"
            fiche = call_deepseek_api(prompt)
            
            # Solution de repli si échec
            if not fiche:
                st.warning("Utilisation du mode de secours...")
                fiche = generate_fallback_report(company, sector)
            
            st.session_state.fiche = fiche
            st.markdown(fiche)

    # Export PDF
    if st.session_state.get('fiche'):
        if st.button("📄 Exporter en PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in st.session_state.fiche.split('\n'):
                # Gestion robuste des caractères spéciaux
                clean_line = line.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 10, clean_line, ln=True)
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                pdf.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button(
                        "Télécharger la fiche PDF",
                        data=f.read(),
                        file_name=f"prospection_{company.replace(' ', '_')[:30]}.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
