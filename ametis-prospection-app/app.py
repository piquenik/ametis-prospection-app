import streamlit as st
import openai
import os
from fpdf import FPDF
import tempfile
import re

# Configuration API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")

st.title("🧐 V1.0 Prospection Ametis.eu")
st.markdown("""
Cet assistant vous permet d'obtenir une fiche complète de prospection enrichie à partir du nom d'une entreprise. Il est conseillé d'indiquer le nom suivi du numero de son département ( ex : Actibio 53 ),cela reste des informations d'analyse IA qui faut Imperativement vérifier

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

# Champs de saisie
nom_entreprise = st.text_input("Entrez le nom de l'entreprise à analyser")

secteur_cible = st.selectbox(
    "Choisissez le secteur d'activité de l'entreprise :",
    [
        "Agroalimentaire",
        "Pharmaceutique",
        "Cosmétique",
        "Logistique / Transport",
        "Electronique / High-Tech",
        "Automobile",
        "Autre industrie"
    ]
)

if st.button("Générer la fiche") and nom_entreprise:
    prompt = f"""
Tu es un assistant IA expert en prospection commerciale B2B pour le compte d’Ametis.eu, spécialiste de :
- la traçabilité industrielle,
- les étiqueteuses et imprimantes industrielles,
- les consommables (étiquettes, rubans transfert thermique),
- l’intégration ERP/WMS et solutions logicielles,
- le mobilier logistique mobile,
- les environnements industriels exigeants (humidité, lavage, IFS/BRC...).

Ton utilisateur est responsable commercial dans le secteur suivant : {secteur_cible}.
L’entreprise cible est : {nom_entreprise}.

Ta mission est de générer une fiche de prospection complète, claire et directement exploitable. Tu dois absolument générer toutes les sections jusqu'à l'étape 8, même en cas d'absence de données concrètes (dans ce cas, fournis des estimations ou des exemples fictifs crédibles).

---

1. Informations de contact :
- Adresse postale complète
- Téléphone général
- Email public (si disponible)
- Effectif estimé
- Site internet (si trouvé)
- Logo (lien image ou site)

2. Présentation synthétique (5 lignes max) :
- Type : fabricant, transformateur, distributeur ?
- Produits ou services
- Marchés visés (GMS, export, RHF...)
- Certifications ou labels (Bio, IFS, BRC...)
- Contraintes industrielles connues (traçabilité, automatisation, hygiène...)

3. Actualités récentes pertinentes :
- Innovations, investissements, recrutement, salon, croissance, certifications...
- Inclure 1 lien source fiable minimum
- Si aucune actualité trouvée, proposer une analyse métier utile (enjeux ou évolution probable)

4. Analyse contextuelle stratégique :
- Urgence ou criticité du besoin
- Profil client : PME, groupe, multisite, bio, artisan...
- Niveau estimé d’investissement ou budget potentiel
- Conseil sur le bon timing / angle d’approche

5. Événements ou salons professionnels fréquentés :
- Nom, type, fréquence, lieu
- Objectif : permettre une accroche ou proposition de RDV

6. Identification des décideurs :
- Recherche croisée LinkedIn, Pappers...
- Nom, fonction, niveau de certitude
- Si absent, générer des profils types crédibles

7. Suggestions d’entreprises voisines à prospecter (rayon 50km) :
- Nom, activité estimée, commune, intérêt pour Ametis

8. Email de prospection combiné Production + Qualité :
- Objet personnalisé
- Introduction contextuelle
- Bloc combiné Production + Qualité
- Appel à action clair

9. Chiffre d’affaires estimé :
- Montant si disponible
- Sinon estimation crédible

⚠️ Génère toujours une fiche, même fictive, basée sur le secteur et la région.
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

            if "7." in fiche:
                start = fiche.find("7.")
                email_section = fiche[start:]
                st.download_button("📋 Copier l’e-mail (en texte)", email_section, file_name="email_prospection.txt")

        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")

# Nettoyage unicode
def nettoyer_texte_unicode(texte):
    return re.sub(r'[^\x00-\x7F]+', '', texte)

# Export PDF
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

# Bloc CSS pour cacher le menu Streamlit, header et footer (usage production)
hide_menu_style = """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)
