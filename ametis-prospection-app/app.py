import streamlit as st
import os
import openai
from fpdf import FPDF
import tempfile
import requests

# Configuration API
openai.api_key = os.getenv("OPENAI_API_KEY")
mistral_api_key = os.getenv("MISTRAL_API_KEY")

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")
st.title("Assistant Prospection Ametis - Comparateur GPT + Mistral")

# Mot de passe obligatoire
password = st.text_input("\U0001F512 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = os.getenv("AMETIS_PASS", "Ametis2025")
if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Formulaire
nom_entreprise = st.text_input("Entrez le nom de l'entreprise à analyser")
secteur_cible = st.selectbox("Secteur d'activité de l'entreprise :", [
    "Agroalimentaire",
    "Pharmaceutique",
    "Cosmétique",
    "Logistique",
    "Electronique",
    "Autre"
])

# Fonction de nettoyage PDF
import re
def nettoyer_texte_unicode(texte):
    return re.sub(r'[^\x00-\x7F]+', '', texte)

# Prompt générique
def construire_prompt(nom_entreprise, secteur_cible):
    return f"""
Tu es un assistant IA expert en prospection commerciale B2B dans le secteur {secteur_cible} pour le compte d’Ametis.eu, spécialiste de :
- la traçabilité industrielle,
- les étiqueteuses et imprimantes industrielles,
- les consommables (étiquettes, rubans transfert thermique),
- l’intégration ERP/WMS,
- le mobilier logistique mobile.

Entreprise cible : {nom_entreprise}.

Fournis une fiche de prospection synthétique comprenant :
1. Coordonnées complètes
2. Présentation en 5 lignes max
3. Actualités pertinentes (avec lien)
4. Analyse stratégique (budget, timing, criticité)
5. Décideurs clés (production + qualité)
6. Suggestions d'entreprises voisines à prospecter
7. Proposition d'email personnalisé (Production + Qualité)
8. Chiffre d’affaires estimé
"""

# Génération de la fiche
if st.button("Générer la fiche") and nom_entreprise:
    prompt = construire_prompt(nom_entreprise, secteur_cible)
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 
