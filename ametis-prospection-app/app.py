import streamlit as st
import openai
import os
from fpdf import FPDF

# Configuration API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Config Streamlit
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")
st.title("🧐 V1.0 Prospection Ametis.eu")
st.markdown("""
Cet assistant vous permet d'obtenir une fiche complète de prospection enrichie à partir du nom d'une entreprise (ex : Actibio 53).
""")

# Protection par mot de passe
password = st.text_input("🔒 Veuillez entrer le mot de passe :", type="password")
CORRECT_PASSWORD = os.getenv("AMETIS_PASS", "Ametis2025")

if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Initialisation de la session
if "fiche_prospection" not in st.session_state:
    st.session_state.fiche_prospection = ""

# Saisie
nom_entreprise = st.text_input("Entrez le nom de l'entreprise + département")

# Prompt
if st.button("Générer la fiche") and nom_entreprise:
    prompt = f"""..."""  # ⬅️ (ici tu mets ton prompt complet inchangé comme plus haut)

    with st.spinner("🔎 Recherche en cours..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un assistant IA spécialisé en prospection B2B pour l'industrie agroalimentaire."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            fiche = response["choices"][0]["message"]["content"]
            st.session_state.fiche_prospection = fiche
            st.markdown("---")
            st.markdown(f"**Fiche pour : {nom_entreprise}**")
            st.markdown(fiche)

            if "✉️" in fiche:
                start = fiche.find("✉️")
                email_section = fiche[start:]
                st.download_button("📋 Copier l’e-mail (en texte)", email_section, file_name="email_prospection.txt")

        except Exception as e:
            st.error(f"Erreur GPT : {e}")

# Affichage si fiche déjà en mémoire
if st.session_state.fiche_prospection:
    st.markdown("---")
    st.markdown("📄 **Exporter la fiche au format PDF**")
    
    if st.button("📥 Télécharger le PDF"):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)

            for line in st.session_state.fiche_prospection.split('\n'):
                pdf.multi_cell(0, 10, line)

            pdf_path = "/tmp/fiche_prospection.pdf"
            pdf.output(pdf_path)

            with open(pdf_path, "rb") as f:
                st.download_button("📄 Télécharger le fichier PDF", f, file_name="fiche_prospection.pdf")

        except Exception as e:
            st.error(f"Erreur PDF : {e}")
