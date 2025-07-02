import streamlit as st
import requests  # Nous utiliserons requests pour appeler l'API DeepSeek
import os
from fpdf import FPDF
import tempfile
import re

# Configuration de l'API DeepSeek
DEEPSEEK_API_KEY = "sk-844f7121c69e471da4933807b23a1b01"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"  # À vérifier selon la doc officielle

# Masquer les éléments Streamlit
st.markdown("""
    <style>
        footer, header {visibility: hidden;}
        [data-testid="stToolbar"] { display: none !important; }
        #MainMenu {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")
st.title("🧐 V1.0 Prospection Ametis.eu")

# Vérification mot de passe
if 'authenticated' not in st.session_state:
    password = st.text_input("🔒 Mot de passe :", type="password")
    if password != "Ametis2025":
        st.warning("Accès restreint")
        st.stop()
    st.session_state.authenticated = True
    st.experimental_rerun()

# Interface principale
nom_entreprise = st.text_input("Entreprise à analyser")
secteur_cible = st.selectbox(
    "Secteur d'activité :",
    ["Agroalimentaire", "Pharma / Cosmétique", "Logistique / Emballage", "Electronique / Technique", "Autre industrie"]
)

if st.button("Générer la fiche") and nom_entreprise:
    prompt = f"""
Tu es un assistant expert en prospection B2B pour Ametis.eu (traçabilité, étiqueteuses industrielles). 
Entreprise cible : {nom_entreprise}. Secteur : {secteur_cible}.

Génère une fiche complète avec :
1. 📌 Coordonnées complètes (logo + site web)
2. 🏢 Présentation synthétique
3. 📰 Actualités/signaux faibles
4. 👥 Contacts clés (production, technique, achats, qualité)
5. ✉️ Email de prospection combiné
6. 📊 Données contextuelles (criticité, budget, stratégie)
7. 🗺️ Carte et suggestions d'entreprises voisines (50km)
"""

    with st.spinner("Génération en cours..."):
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Expert en prospection B2B"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data).json()
            fiche = response['choices'][0]['message']['content']
            
            st.session_state.fiche = fiche
            st.markdown("---")
            st.markdown(fiche)

        except Exception as e:
            st.error(f"Erreur : {e}")

# Export PDF
if 'fiche' in st.session_state:
    if st.button("📥 Exporter en PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        for line in st.session_state.fiche.split('\n'):
            pdf.cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button(
                    label="Télécharger PDF",
                    data=f,
                    file_name=f"fiche_{nom_entreprise.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
