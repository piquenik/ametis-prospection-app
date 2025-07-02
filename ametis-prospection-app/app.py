import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile
import socket

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

# Nouveau modèle à tester
MODEL_NAME = "deepseek-coder"  # <--- CHANGEMENT IMPORTANT ICI
API_URL = "https://api.deepseek.ai/v1/chat/completions"

# Fonction API pour le nouveau modèle
def call_deepseek_api(prompt, max_retries=1):
    """Tentative avec le modèle deepseek-coder"""
    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,  # Utilisation du nouveau modèle
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            st.warning(f"Erreur API (HTTP {response.status_code}): {response.text[:200]}")
            return None
            
    except Exception as e:
        st.error(f"Erreur de connexion : {str(e)[:100]}")
        return None

# Solution de repli locale
def generate_fallback_report(company, sector):
    return f"""
# 🧐 Fiche Prospection: {company}

**Secteur:** {sector}  
**Date de génération:** {time.strftime("%d/%m/%Y")}
**Modèle utilisé:** {MODEL_NAME} (fallback local)

## 📌 Coordonnées
- **Adresse:** Non disponible
- **Site web:** www.{company.replace(' ', '').lower()}.fr
- **Téléphone:** 01 23 45 67 89

## 🏢 Activité principale
Entreprise spécialisée dans le secteur {sector.lower()}. 

## 👥 Contacts clés
- **Responsable production:** contact@{company.replace(' ', '').lower()}.fr
- **Responsable qualité:** qualite@{company.replace(' ', '').lower()}.fr

## ✉️ Email de prospection
> Objet: Solution de traçabilité pour votre production  
>  
> Bonjour,  
>  
> Nous proposons des solutions innovantes adaptées à votre secteur d'activité.  
> Pouvons-nous échanger la semaine prochaine?  
>  
> Cordialement,  
> [Votre nom]  
> Ametis.eu
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
    st.title("🧐 Assistant Prospection Ametis")
    st.caption(f"Modèle: {MODEL_NAME}")
    
    company = st.text_input("Nom de l'entreprise", "ACTIBIO 53")
    sector = st.selectbox("Secteur", ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", "Industrie", "Autre"], index=0)
    
    if st.button("Générer la fiche", type="primary"):
        if not company:
            st.warning("Veuillez saisir un nom d'entreprise")
            return
            
        with st.spinner("Génération en cours..."):
            # Prompt optimisé pour deepseek-coder
            prompt = f"""
Tu es un expert en prospection commerciale. Génère une fiche entreprise au format Markdown pour:
- Entreprise: {company}
- Secteur: {sector}

La fiche doit contenir:
1. Coordonnées complètes (adresse fictive mais plausible)
2. Description de l'activité (2-3 phrases)
3. 2 contacts clés avec emails
4. Un email de prospection court
5. Analyse des besoins potentiels

Sois concis et professionnel.
"""
            
            # Tentative avec le nouveau modèle
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
                # Nettoyage des caractères spéciaux
                clean_line = line.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(0, 8, clean_line, ln=True)
            
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
