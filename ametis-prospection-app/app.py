import streamlit as st
import requests
import os
import time

# Configuration de la page
st.set_page_config(
    page_title="Assistant Prospection Ametis PRO",
    layout="centered",
    page_icon="🔍"
)
st.title("🔍 Assistant Prospection Ametis PRO")

# --- Authentification ---
password = st.text_input("🔒 Mot de passe d'accès :", type="password")
CORRECT_PASSWORD = os.getenv("APP_PASSWORD", "Ametis2025")

if password != CORRECT_PASSWORD:
    st.error("Accès non autorisé - mot de passe incorrect")
    st.stop()

# --- Paramètres de recherche ---
with st.expander("⚙️ Paramètres avancés", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Précision (température)", 0.1, 1.0, 0.6)
    with col2:
        max_tokens = st.slider("Longueur réponse", 500, 2000, 1200)

# --- Saisie utilisateur ---
nom_entreprise = st.text_input("Nom de l'entreprise*")
secteur_cible = st.selectbox(
    "Secteur d'activité*",
    ["Agroalimentaire", "Pharma/Cosmétique", "Logistique/Emballage", 
     "Electronique/Technique", "Autre industrie"]
)

# --- Boutons d'action ---
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    btn_standard = st.button("🔎 Recherche standard", type="primary")
with col2:
    btn_pro = st.button("🚀 Recherche PRO", type="secondary")
with col3:
    st.caption("*Champs obligatoires")

# --- Configuration API ---
endpoint = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"
}

# --- Prompt expert CORRIGÉ ---
PROMPT_EXPERT = f"""
Tu es un analyste B2B expert pour Ametis. Génère une fiche entreprise ultra-précise pour :
- Entreprise : {nom_entreprise}
- Secteur : {secteur_cible}

### Exigences strictes :
1. Structure Markdown EXACTE comme dans le template
2. Sources vérifiables pour tous les chiffres
3. Contacts réels uniquement (sinon "Non trouvé")
4. Analyse industrielle pertinente

### Template OBLIGATOIRE :
```markdown
### 1. Résumé synthétique
[🏢 Secteur] | [📍 Localisation] 
[1 phrase combinant secteur et localisation]

### 2. Description activité
[2-3 phrases maximum]
- Activité principale : [détail]
- Spécialités : [liste à puces]
- Positionnement : [1 phrase]

### 3. Chiffres clés
📊 CA : [valeur] | 📈 Tendance
👥 Effectifs : [nombre]
🏭 Sites : [nombre]
ℹ️ Source : [lien]

### 4. Signaux récents
📰 Derniers 6 mois
- [Événement 1 avec date]
- [Événement 2 avec date]
- Analyse : [1 phrase]

### 5. Contacts
🔍 Recherche vérifiée
- Production : [Nom] | [Contact] | [Tel]
- Qualité : [Nom] | [Contact] | [Tel]
- Technique : [Nom] | [Contact] | [Tel]
