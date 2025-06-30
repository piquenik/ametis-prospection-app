import streamlit as st
import os
from fpdf import FPDF
import tempfile
import re
import requests

# Configuration API
openai_api_key = os.getenv("OPENAI_API_KEY")
mistral_api_key = os.getenv("MISTRAL_API_KEY")

# Configuration page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")
st.title("🧐 V1.0 Prospection Ametis.eu")

st.markdown("""
### Comparaison des réponses IA : ChatGPT vs Mistral

Cette section vous permet de comparer les résultats générés par deux modèles d'intelligence artificielle :
- 🤖 **ChatGPT (OpenAI)** : spécialisé dans la prospection B2B pour Ametis.eu
- 🔍 **Mistral** : pour analyse comparative ou approche alternative

Entrez le nom d'une entreprise pour générer et comparer les deux réponses.
""")

# Mot de passe
password = st.text_input("🔒 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = os.getenv("AMETIS_PASS", "Ametis2025")
if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Champs de saisie
nom_entreprise = st.text_input("Entrez le nom de l'entreprise à analyser")
secteur_cible = st.selectbox(
    "Choisissez le secteur d'activité de l'entreprise :",
    ["Agroalimentaire", "Cosmétique", "Pharma", "Logistique", "Autre industrie"]
)

# Prompt de base
def generer_prompt(nom_entreprise, secteur):
    return f"""
Tu es un assistant IA expert en prospection B2B dans le secteur **{secteur}**. L’entreprise cible est : **{nom_entreprise}**.

Ta mission : générer une fiche de prospection synthétique et exploitable incluant :
1. Coordonnées générales
2. Présentation de l’activité
3. Dernières actualités pertinentes
4. Décideurs clés
5. Analyse contextuelle et proposition de valeur pour Ametis.eu
6. Entreprises voisines à prospecter (rayon 50 km)
7. Email de prospection combiné (production + qualité)

⚠️ Si les données sont absentes, simule des informations crédibles.
"""

# Appel OpenAI
def call_chatgpt(prompt):
    import openai
    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Assistant de prospection B2B Ametis"}, {"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2500
    )
    return response.choices[0].message.content

# Appel Mistral
def call_mistral(prompt):
    headers = {
        "Authorization": f"Bearer {mistral_api_key}",
        "Content-Type": "application/json"
    }
    json_data = {
        "model": "mistral-medium",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2500
    }
    response = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=json_data)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

# Nettoyage PDF
def nettoyer_texte_unicode(texte):
    return re.sub(r'[^\x00-\x7F]+', '', texte)

# Lancer génération
if st.button("Générer la fiche") and nom_entreprise:
    prompt = generer_prompt(nom_entreprise, secteur_cible)
    st.info("Génération en cours...")

    try:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🤖 Réponse ChatGPT")
            output_chatgpt = call_chatgpt(prompt)
            st.session_state.fiche_chatgpt = output_chatgpt
            st.markdown(output_chatgpt)

        with col2:
            st.subheader("🔍 Réponse Mistral")
            output_mistral = call_mistral(prompt)
            st.session_state.fiche_mistral = output_mistral
            st.markdown(output_mistral)

    except Exception as e:
        st.error(f"Erreur lors de la génération : {e}")

# Export PDF (ChatGPT)
if "fiche_chatgpt" in st.session_state:
    st.markdown("📄 **Générer la fiche ChatGPT au format PDF**")
    if st.button("📥 Télécharger le PDF (ChatGPT)"):
        try:
            texte_nettoye = nettoyer_texte_unicode(st.session_state.fiche_chatgpt)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for line in texte_nettoye.split('\n'):
                pdf.multi_cell(0, 10, line)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                pdf.output(tmpfile.name)
                tmpfile.seek(0)
                st.download_button(
                    label="📄 Télécharger le fichier PDF",
                    data=tmpfile.read(),
                    file_name=f"fiche_prospection_chatgpt_{nom_entreprise.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Erreur lors de la génération du PDF : {e}")
