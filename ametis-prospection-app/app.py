import streamlit as st
import openai
import os
from fpdf import FPDF
import tempfile
import re

# Bloc CSS pour masquer le header, footer, bouton Manage App et menu Streamlit
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

# Configuration API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")

st.title("🧐 V1.0 Prospection Ametis.eu")
st.markdown("""
Cet assistant vous permet d'obtenir une fiche complète de prospection enrichie à partir du nom d'une entreprise. Il est conseillé d'indiquer le nom suivi du numero de son département ( ex : Actibio 53 ), cela reste des informations d'analyse IA qui faut impérativement vérifier

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
password = st.text_input("🔒 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = os.getenv("AMETIS_PASS", "Ametis2025")

if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Champ de saisie
nom_entreprise = st.text_input("Entrez le nom de l'entreprise à analyser")

secteur_cible = st.selectbox(
    "Choisissez le secteur d'activité de l'entreprise :",
    ["Agroalimentaire", "Pharma / Cosmétique", "Logistique / Emballage", "Electronique / Technique", "Autre industrie"]
)

# Génération de la fiche
if st.button("Générer la fiche") and nom_entreprise:
    prompt = f"""
Tu es un assistant IA expert en prospection commerciale B2B pour le compte d’Ametis.eu, spécialisée dans la traçabilité, les étiqueteuses industrielles, les consommables, et l’intégration ERP/WMS. L’entreprise cible est : {nom_entreprise}. Secteur : {secteur_cible}.

Génère une fiche complète et directement exploitable même si certaines données doivent être simulées. Ne laisse jamais de section vide.

[...LE RESTE DU PROMPT DE FICHE ICI — ne change rien à cette partie s’il est déjà correct...]
"""

    with st.spinner("Recherche en cours et génération de la fiche..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un assistant IA spécialisé en prospection B2B."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            fiche = response["choices"][0]["message"]["content"]
            st.session_state.fiche = fiche
            st.markdown("---")
            st.markdown(f"**Fiche pour : {nom_entreprise}**")
            st.markdown(fiche)

            if "✉️ 7." in fiche:
                start = fiche.find("✉️ 7.")
                email_section = fiche[start:]
                st.download_button("📋 Copier l’e-mail (en texte)", email_section, file_name="email_prospection.txt")

        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")

# Export PDF
def nettoyer_texte_unicode(texte):
    return re.sub(r'[^\x00-\x7F]+', '', texte)

if "fiche" in st.session_state and st.session_state.fiche:
    st.markdown("📄 **Génerer la fiche au format PDF**")

    if st.button("📥 Télécharger le PDF"):
        try:
            texte_nettoye = nettoyer_texte_unicode(st.session_state.fiche)

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
                    file_name=f"fiche_prospection_{nom_entreprise.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
        except Exception as e:
            st.error(f"Erreur lors de la génération du PDF : {e}")
else:
    st.info("Entrez un nom d'entreprise pour générer une fiche.")
