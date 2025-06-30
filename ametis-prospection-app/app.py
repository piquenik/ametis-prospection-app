import streamlit as st
import openai
import requests
import os

# Configuration API
openai.api_key = os.getenv("OPENAI_API_KEY")
mistral_api_key = os.getenv("MISTRAL_API_KEY")

# Configuration de la page
st.set_page_config(page_title="Comparateur Mistral vs ChatGPT", layout="centered")
st.title("🧠 Comparateur IA : ChatGPT vs Mistral")

st.markdown("""
Compare les réponses des deux IA pour une même question commerciale, afin de choisir la formulation ou l'argumentaire le plus adapté.
""")

# Saisie utilisateur
entreprise = st.text_input("Nom de l'entreprise à analyser (ex : Actibio 53)")
secteur = st.text_input("Secteur d'activité cible (ex : agroalimentaire, cosmétique, logistique...)", value="agroalimentaire")

if st.button("Comparer les IA") and entreprise:

    prompt = f"""
Tu es un assistant IA expert en prospection commerciale B2B pour Ametis.eu, spécialiste de la traçabilité industrielle, des imprimantes et étiqueteuses, et des environnements exigeants.

Secteur cible : {secteur}
Entreprise à analyser : {entreprise}

Fournis une fiche synthétique de prospection (max 800 tokens) comprenant :
1. Coordonnées (adresse, téléphone, mail, site)
2. Présentation activité (4 lignes max)
3. Actualité ou analyse pertinente
4. Identification de 2 à 3 décideurs (nom + fonction, si trouvés)
5. Proposition d'email combiné Production + Qualité (structure pro, appel à action clair)
"""

    st.info("🔄 Génération en cours...")

    # ChatGPT
    try:
        chatgpt_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant expert en prospection B2B."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        chatgpt_output = chatgpt_response.choices[0].message.content
    except Exception as e:
        chatgpt_output = f"Erreur ChatGPT : {e}"

    # Mistral
    try:
        mistral_headers = {
            "Authorization": f"Bearer {mistral_api_key}",
            "Content-Type": "application/json"
        }
        mistral_data = {
            "model": "mistral-medium",
            "messages": [
                {"role": "system", "content": "Tu es un assistant expert en prospection B2B."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        mistral_response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=mistral_headers, json=mistral_data)
        mistral_output = mistral_response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        mistral_output = f"Erreur Mistral : {e}"

    # Affichage
    st.markdown("## 🤖 Résultat ChatGPT")
    st.markdown(chatgpt_output)

    st.markdown("---")

    st.markdown("## 🦊 Résultat Mistral")
    st.markdown(mistral_output)

    st.markdown("---")
    st.success("Comparaison terminée. Analysez les différences de ton, de pertinence et de style.")
