import streamlit as st
import requests
import os
import time

# Configuration de la page
st.set_page_config(
    page_title="Assistant Prospection Ametis",
    layout="centered",
    page_icon="📊"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-container {
        max-width: 900px;
        padding: 2rem;
    }
    .report-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 2rem;
        margin-top: 1rem;
        word-wrap: break-word;
    }
    @media (max-width: 640px) {
        .main-container {
            padding: 1rem;
        }
        .report-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Authentification
def check_password():
    password = st.text_input("🔒 Mot de passe d'accès :", type="password")
    if password != os.getenv("APP_PASSWORD", "Ametis2025"):
        st.error("Accès non autorisé")
        st.stop()
    return True

if not check_password():
    st.stop()

# Header
st.title("📊 Assistant Prospection Ametis")
st.markdown("---")

# Paramètres
with st.expander("⚙️ Paramètres avancés", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Niveau de précision", 0.1, 1.0, 0.6)
    with col2:
        max_tokens = st.slider("Longueur de réponse", 500, 2000, 1200)

# Formulaire de recherche
with st.form("recherche_form"):
    nom_entreprise = st.text_input("Nom de l'entreprise* ( preciser nom de l'entreprise + ville + departement (idealement)")
    secteur_cible = st.selectbox(
        "Secteur d'activité*",
        ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", 
         "Electronique/Technique", "Autre"]
    )
    
    col1, col2 = st.columns(2)
    with col1:
        recherche_standard = st.form_submit_button("🔍 Recherche Standard")
    with col2:
        recherche_pro = st.form_submit_button("🚀 Recherche PRO")

# Configuration API
def generate_prompt(entreprise, secteur):
    return f"""Génère une fiche entreprise structurée pour :
- Entreprise: {entreprise}
- Secteur: {secteur}

### Structure requise:
1. **Résumé** (secteur + localisation)
2. **Activité** (description courte)
3. **Chiffres** (CA, effectifs, sites)
4. **Actualité** (2-3 événements récents)
5. **Contacts** (noms vérifiés uniquement)

Format Markdown strict."""

# Traitement de la recherche
if recherche_standard or recherche_pro:
    with st.spinner("Analyse en cours..."):
        payload = {
            "model": "deepseek-reasoner" if recherche_pro else "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Expert en analyse B2B"},
                {"role": "user", "content": generate_prompt(nom_entreprise, secteur_cible)}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "web_search": recherche_pro
        }

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
                json=payload,
                timeout=120 if recherche_pro else 60
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Affichage du résultat dans un conteneur adaptatif
                st.markdown("---")
                st.success("✅ Analyse terminée")
                
                with st.container():
                    st.markdown(
                        f'<div class="report-container">{content}</div>',
                        unsafe_allow_html=True
                    )
                
                if recherche_pro:
                    st.info("🌐 Recherche web activée | Mode approfondi")
            else:
                st.error(f"Erreur API: {response.status_code}")

        except Exception as e:
            st.error(f"Erreur: {str(e)}")

# Sidebar
with st.sidebar:
    st.info("""
    **Instructions:**
    1. Renseignez le nom de l'entreprise
    2. Sélectionnez le secteur
    3. Lancez la recherche
    """)
    if st.button("🔄 Réinitialiser"):
        st.rerun()
