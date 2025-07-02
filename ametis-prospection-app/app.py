import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile
import os

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

# Fonction API robuste avec gestion avancée des timeouts
def call_deepseek_api(prompt, max_retries=3):
    """Fonction optimisée pour la résilience avec retry et fallback"""
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 1500  # Réduit pour accélérer la réponse
                },
                timeout=(3.05, 30)  # Connect: 3s, Read: 30s
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                st.warning(f"Tentative {attempt+1} échouée (HTTP {response.status_code})")
                
        except requests.exceptions.Timeout:
            st.warning(f"Tentative {attempt+1} : Timeout - Réessai...")
            time.sleep(1)  # Pause avant réessai
            
        except Exception as e:
            st.error(f"Erreur : {str(e)[:100]}")
            return None
    
    # Si toutes les tentatives échouent
    st.error("Échec après plusieurs tentatives. Solutions:")
    st.markdown("""
    1. Réessayez dans 1-2 minutes
    2. Vérifiez votre connexion Internet
    3. Contactez le support DeepSeek
    """)
    return None

# Solution de repli locale
def generate_fallback_report(company, sector):
    """Génère un rapport basique quand l'API échoue"""
    return f"""
# Fiche Prospection: {company}

**Secteur:** {sector}

## Coordonnées
- Adresse: Non disponible (erreur API)
- Site web: www.{company.replace(' ', '').lower()}.fr
- Téléphone: 01 23 45 67 89

## Activité
Description générée localement - L'API DeepSeek n'a pas répondu dans le délai imparti.

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
            # Tentative API
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
                pdf.cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                pdf.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button(
                        "Télécharger la fiche PDF",
                        data=f.read(),
                        file_name=f"prospection_{company.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
