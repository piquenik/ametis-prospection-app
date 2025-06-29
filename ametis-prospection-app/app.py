import streamlit as st
import openai
import os
from fpdf import FPDF
import tempfile
import smtplib
from email.message import EmailMessage

# Configuration API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")

st.title("\U0001F9D0 V1.0 Prospection Ametis.eu")
st.markdown("""
Cet assistant vous permet d'obtenir une fiche complète de prospection enrichie à partir du nom d'une entreprise. Il est conseillé d'indiquer le nom suivi du numéro de son département (ex : Actibio 53)

Chaque fiche inclut :
- Les coordonnées complètes et visuelles (logo + site web)
- Une présentation synthétique de l’activité
- Les actualités ou signaux faibles de transformation
- Les contacts clés (production, technique, achats, qualité)
- Un email de prospection combiné (production + qualité)
- Des données contextuelles : criticité du besoin, profil client, budget estimé, stratégie d’approche
- Une carte et suggestions d'entreprises voisines dans un rayon de 50 km
""")

# Mot de passe obligatoire
password = st.text_input("\U0001F512 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = os.getenv("AMETIS_PASS", "Ametis2025")

if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Champ de saisie de l'entreprise
nom_entreprise = st.text_input("Entrez le nom de l'entreprise à analyser")

if st.button("Générer la fiche") and nom_entreprise:
    prompt = f"""
    [TON PROMPT ACTUEL ICI, identique au bloc précédent]
    """

    with st.spinner("Recherche en cours et génération de la fiche..."):
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
            st.markdown("---")
            st.markdown(f"**Fiche pour : {nom_entreprise}**")
            st.markdown(fiche)

            if "✉️ 7." in fiche:
                start = fiche.find("✉️ 7.")
                email_section = fiche[start:]
                st.download_button("\U0001F4CB Copier l’e-mail (en texte)", email_section, file_name="email_prospection.txt")

            # Export PDF
            st.markdown("### \U0001F4E4 Export PDF")
            email_export = st.text_input("Adresse e-mail pour l'exportation PDF :")
            if st.button("Envoyer le PDF") and email_export:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Arial", size=10)
                for line in fiche.splitlines():
                    pdf.multi_cell(0, 8, line)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf.output(tmp_file.name)
                    tmp_file_path = tmp_file.name

                msg = EmailMessage()
                msg["Subject"] = f"Fiche de prospection Ametis - {nom_entreprise}"
                msg["From"] = os.getenv("EMAIL_FROM")
                msg["To"] = email_export
                msg.set_content(f"Bonjour,\n\nVeuillez trouver ci-joint la fiche de prospection générée pour l'entreprise {nom_entreprise}.\n\nCordialement,\nAssistant Ametis")
                with open(tmp_file_path, "rb") as f:
                    msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=f"fiche_{nom_entreprise}.pdf")

                with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                    smtp.starttls()
                    smtp.login(os.getenv("EMAIL_FROM"), os.getenv("EMAIL_PASSWORD"))
                    smtp.send_message(msg)
                st.success("PDF envoyé avec succès !")

        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
else:
    st.info("Entrez un nom d'entreprise pour générer une fiche.")
