import streamlit as st
import requests
import os
import time
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")
st.title("🥸 Assistant Prospection Ametis")

# Mot de passe obligatoire
password = st.text_input("🔒 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = os.getenv("APP_PASSWORD", "Ametis2025")

if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Saisie utilisateur
nom_entreprise = st.text_input("Nom de l'entreprise")
secteur_cible = st.selectbox("Secteur", ["Agroalimentaire", "Pharma / Cosmétique", "Logistique / Emballage", "Electronique / Technique", "Autre industrie"])

col1, col2 = st.columns([2, 2])
with col1:
    lancer_recherche = st.button("Générer la fiche")
with col2:
    recherche_approfondie = st.button("Recherche approfondie")

if lancer_recherche or recherche_approfondie:
    endpoint = "https://api.deepseek.com/v1/chat/completions"
    model = "deepseek-chat"

    if recherche_approfondie:
        model = "deepseek-reasoner"
        st.markdown("ℹ️ La recherche approfondie peut prendre plus de temps. Source : Sales Navigator ou Lusha.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"
    }

    prompt = f"""
Tu es un expert en prospection commerciale. Génère une fiche entreprise au format Markdown pour : {nom_entreprise} ({secteur_cible}).

Structure :
1. Résumé synthétique (secteur + localisation)
2. Description de l'activité (2–3 phrases)
3. Chiffres clés s'ils sont publics (CA, effectifs, usines...)
4. Signaux d'actualité ou transformation industrielle
5. Recherche active de contacts : responsable qualité, production, technique, achats, marketing. S'ils ne sont pas trouvables, indique clairement : "Contact non trouvé, essayer de faire une recherche approfondie."
    """

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es un assistant IA expert en prospection B2B."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 900
    }

    with st.spinner(f"🧠 Réflexion en cours, via : {endpoint}"):
        progress_bar = st.progress(0)
        compteur = st.empty()
        start_time = time.time()

        for i in range(60):
            time.sleep(1)
            progress_bar.progress((i + 1) / 60)
            compteur.markdown(f"🕒 Temps écoulé : {i + 1} sec")

        try:
            response = requests.post(endpoint, headers=headers, json=data, timeout=45)
            st.markdown("---")
            st.markdown(f"📡 Code HTTP : {response.status_code}")

            if response.status_code == 200:
                try:
                    content = response.json()["choices"][0]["message"]["content"]
                    if content.strip():
                        st.success("✅ Contenu reçu :")
                        st.markdown("<div style='white-space: pre-wrap; word-wrap: break-word;'>" + content + "</div>", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Réponse reçue mais vide.")
                except Exception as e:
                    st.error(f"Erreur de parsing de la réponse : {e}")
                    st.json(response.json())
            else:
                st.error("❌ Réponse invalide ou vide")

        except Exception as e:
            st.error(f"❌ Exception levée : {e}")
