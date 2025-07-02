import streamlit as st
import requests
import os
import time
from fpdf import FPDF
import tempfile
import re

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")

# Variables d'environnement sécurisées (secrets Streamlit)
API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
APP_PASSWORD = st.secrets.get("APP_PASSWORD", "Ametis2025")
FORCED_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"

# Masquer interface Streamlit
st.markdown("""
    <style>
        footer, header {visibility: hidden;}
        [data-testid="stToolbar"] { display: none !important; }
        #MainMenu {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none !important;}
    </style>
    <script>
        const interval = setInterval(() => {
            const toolbar = window.parent.document.querySelector('[data-testid="stToolbar"]');
            if (toolbar) {
                toolbar.style.display = 'none';
            }
            const badge = window.parent.document.querySelector('.viewerBadge_container__1QSob');
            if (badge) {
                badge.style.display = 'none';
                clearInterval(interval);
            }
        }, 100);
    </script>
""", unsafe_allow_html=True)

st.title("🧐 Assistant Prospection Ametis")

# Authentification
password = st.text_input("🔒 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
if password != APP_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Formulaire utilisateur
st.subheader("Nom de l'entreprise")
nom_entreprise = st.text_input("", placeholder="ex : ACTIBIO 53")

secteur = st.selectbox("Secteur", [
    "Agroalimentaire", "Pharma / Cosmétique", "Logistique / Emballage",
    "Electronique / Technique", "Autre industrie"
])

if st.button("Générer la fiche") and nom_entreprise:
    prompt = f"""
Tu es un expert en prospection commerciale. Génère une fiche entreprise au format Markdown pour : {nom_entreprise}. Secteur : {secteur}

Structure :
1. Résumé synthétique de l’entreprise (1-2 phrases)
2. Description de l\'activité (2-3 phrases)
3. Chiffres clés connus ou estimés (effectif, CA...)
4. Positionnement marché et engagements (durabilité, innovation...)
5. Contacts clés :
   | Fonction               | Nom (si connu)       | Source/Note            |
   |------------------------|----------------------|-------------------------|
   | Responsable production| ...                  | ...                     |
   | Responsable qualité   | ...                  | ...                     |
   | Responsable technique | ...                  | ...                     |
   | Responsable achats    | ...                  | ...                     |
   | Responsable marketing | ...                  | ...                     |

Note : si un contact est introuvable, mentionne explicitement "Non identifié publiquement".
"""

    with st.container():
        st.markdown(f"""🧠 **Réflexion en cours, via :** [{FORCED_ENDPOINT}]({FORCED_ENDPOINT})""")
        progress = st.progress(0)

        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1800
            }

            with st.spinner("Appel en cours..."):
                response = requests.post(FORCED_ENDPOINT, headers=headers, json=payload, timeout=60)
                progress.progress(100)

            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                st.success("✅ Contenu reçu :")
                st.markdown(content)
            else:
                st.error("❌ Réponse invalide de l’API")
                st.code(response.text)

        except Exception as e:
            st.error(f"❌ Exception levée : {e}")
