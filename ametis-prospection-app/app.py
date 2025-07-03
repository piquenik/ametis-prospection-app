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

# --- Prompt expert REVISÉ et TESTÉ ---
PROMPT_TEMPLATE = """Tu es un analyste B2B expert pour Ametis. Génère une fiche entreprise ultra-précise pour :
- Entreprise : {entreprise}
- Secteur : {secteur}

### Exigences strictes :
1. Structure Markdown EXACTE comme dans le template
2. Sources vérifiables pour tous les chiffres
3. Contacts réels uniquement (sinon "Non trouvé")

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
```"""

# Formatage séparé pour éviter les problèmes de f-string
PROMPT_EXPERT = PROMPT_TEMPLATE.format(entreprise=nom_entreprise, secteur=secteur_cible)

if btn_standard or btn_pro:
    # --- Configuration de la requête ---
    payload = {
        "model": "deepseek-reasoner" if btn_pro else "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "Tu es un assistant expert en intelligence économique B2B. Réponses factuelles et structurées."
            },
            {"role": "user", "content": PROMPT_EXPERT}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "web_search": btn_pro
    }

    # --- Execution ---
    with st.status("🔍 Analyse en cours...", expanded=True) as status:
        try:
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.03 if btn_pro else 0.01)
                progress_bar.progress(i + 1)

            timeout = 120 if btn_pro else 60
            response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                st.success(f"✅ Analyse terminée (Tokens: {result['usage']['total_tokens']})")
                if btn_pro:
                    st.info("🌐 Recherche web activée | Mode Reasoner R1")
                
                st.divider()
                st.markdown(content)
                
            else:
                st.error(f"Erreur API {response.status_code}")
                st.code(response.text, language="json")

        except Exception as e:
            st.error(f"Erreur : {str(e)}")
        finally:
            status.update(label="Analyse complète", state="complete")

# --- Sidebar ---
with st.sidebar:
    st.header("Journal")
    st.code(f"Dernière requête:\n{time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Entreprise: {nom_entreprise}\n"
            f"Mode: {'PRO' if btn_pro else 'Standard'}")
