import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile
import socket
import json
from datetime import datetime
import random

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

# Endpoint unique forcé
API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"

# Fonction API robuste avec timeout étendu et affichage brut
def call_deepseek_api(prompt):
    try:
        start_time = time.time()
        response = requests.post(
            API_ENDPOINT,
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
            timeout=30
        )
        response_time = time.time() - start_time
        return response, response_time

    except Exception as e:
        return None, str(e)

# Fallback local
def generate_fallback_report(company, sector):
    villes = ["Laval", "Angers", "Nantes", "Rennes", "Le Mans"]
    return f"""
# 🧐 Fiche Prospection: {company}
**Secteur:** {sector}  
**Date de génération:** {datetime.now().strftime("%d/%m/%Y %H:%M")}  
**Source:** Mode local Ametis

## 📌 Coordonnées
- **Adresse:** {random.randint(1,99)} rue des Entrepreneurs, {random.randint(44000,44999)} {random.choice(villes)}
- **Site web:** www.{company.lower().replace(' ','')}.fr
- **Téléphone:** 02 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}

## 🏢 Activité principale
Entreprise spécialisée dans le secteur {sector.lower()}. 

## 👥 Contacts clés
- **Responsable production:** production.{company.lower().replace(' ','')}@example.com
- **Responsable qualité:** qualite.{company.lower().replace(' ','')}@example.com
- **Responsable achats:** achats.{company.lower().replace(' ','')}@example.com

## ✉️ Email de prospection
> Bonjour,\n\nNous pensons que nos solutions de traçabilité Ametis pourraient optimiser vos processus.\n\nNous proposons:\n- Étiqueteuses industrielles haute performance\n- Systèmes de traçabilité temps réel\n- Intégration ERP/WMS\n\nPouvons-nous planifier un court échange la semaine prochaine ?\n\nCordialement,\n[Votre nom] – contact@ametis.eu"

# Interface principale
def main():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.title("🔒 Authentification")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Valider"):
            if password == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Accès refusé")
        st.stop()

    st.title("🧐 Assistant Prospection Ametis")
    st.caption("Mode API direct forcé")

    company = st.text_input("Nom de l'entreprise", "ACTIBIO 53")
    sector = st.selectbox("Secteur", ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", "Industrie", "Autre"], index=0)

    if st.button("Générer la fiche", type="primary"):
        if not company:
            st.warning("Veuillez saisir un nom d'entreprise")
            return

        with st.spinner("🧠 Réflexion en cours, via : " + API_ENDPOINT):
            prompt = f"""
Tu es un expert en prospection commerciale. Génère une fiche entreprise au format Markdown pour :
- Entreprise: {company}
- Secteur: {sector}

La fiche doit contenir :
1. Coordonnées complètes (adresse fictive mais plausible)
2. Description de l\'activité (2-3 phrases)
3. 2 à 3 contacts clés si possibles (production, qualité, technique, marketing, achats)
4. Un email de prospection court
5. Analyse des besoins potentiels
Sois concis et professionnel.
"""

            with st.empty():
                bar = st.progress(0)
                for i in range(10):
                    time.sleep(0.1)
                    bar.progress((i + 1) * 10)

            response, info = call_deepseek_api(prompt)
            if response and response.status_code == 200:
                try:
                    content = response.json()["choices"][0]["message"]["content"]
                    st.success("✅ Contenu reçu :")
                    st.markdown(content)
                except:
                    st.error("⚠️ Réponse inattendue")
                    st.code(response.text)
            else:
                st.error(f"❌ Erreur API : {info}")
                st.warning("Utilisation du mode local")
                fiche = generate_fallback_report(company, sector)
                st.markdown(fiche)

if __name__ == "__main__":
    main()
