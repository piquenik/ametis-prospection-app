import streamlit as st
import requests
import os
import time
from fpdf import FPDF
import tempfile
import re

# Configuration API
API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
API_TIMEOUT = 60  # Timeout en secondes
API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")

# Masquer header Streamlit
st.markdown("""
    <style>
        footer, header {visibility: hidden;}
        [data-testid="stToolbar"] { display: none !important; }
        #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🧐 Assistant Prospection Ametis")

# Mot de passe obligatoire
password = st.text_input("🔒 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = st.secrets.get("APP_PASSWORD", "Ametis2025")
if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Champs
nom_entreprise = st.text_input("Nom de l'entreprise")
secteur_cible = st.selectbox("Secteur", [
    "Agroalimentaire",
    "Pharma / Cosmétique",
    "Logistique / Emballage",
    "Electronique / Technique",
    "Autre industrie"])

if st.button("Générer la fiche") and nom_entreprise:
    prompt = f"""
Tu es un expert en prospection commerciale. Génère une fiche entreprise au format Markdown pour : {nom_entreprise}, secteur : {secteur_cible}.

Contenu demandé :
1. Résumé synthétique (ville + activité)
2. Description de l'activité (2-3 phrases)
3. Points différenciants, chiffres clés, innovations, labels éventuels
4. Actualités marquantes ou signaux de transition (ESG, croissance, réorg)
5. Liste les contacts professionnels trouvables (priorité : Responsable Production, Qualité, Technique, Achats, Maintenance, Marketing)
6. Faits intéressants à exploiter pour une approche Ametis
7. Proposition d’e-mail de prospection combiné (technique + qualité)
    """

    st.info(f"🧠 Réflexion en cours, via : [{API_ENDPOINT}]({API_ENDPOINT})")

    # Barre de progression avec minuteur
    progress_bar = st.progress(0)
    timer_placeholder = st.empty()
    start_time = time.time()

    for i in range(61):
        elapsed = int(time.time() - start_time)
        progress_bar.progress(min(i / 60, 1.0))
        timer_placeholder.markdown(f"⏱ Temps écoulé : {elapsed} sec")
        time.sleep(1)
        if elapsed >= API_TIMEOUT:
            break

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=API_TIMEOUT)
        st.write(f"📡 Code HTTP : {response.status_code}")

        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            st.success("✅ Contenu reçu :")
            st.markdown(content)
        else:
            st.error("❌ Échec DeepSeek – réponse invalide")
            st.code(response.text)

    except Exception as e:
        st.error(f"❌ Exception levée : {e}")
