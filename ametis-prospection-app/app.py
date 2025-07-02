import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile
import re
from datetime import datetime

# Configuration
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "Ametis2025")
except:
    st.error("Erreur de configuration")
    st.stop()

# Endpoints API
API_ENDPOINTS = [
    "https://api.deepseek.com/v1/chat/completions",
    "https://gateway.deepseek.com/chat/completions"
]

# Fonction pour tester connectivité
def test_endpoint(endpoint):
    try:
        test_url = endpoint.replace("/chat/completions", "")
        response = requests.get(test_url, timeout=5)
        return response.status_code == 200
    except:
        return False

# Fonction pour appel API DeepSeek
def call_deepseek_api(prompt, endpoint_index=0):
    endpoint = API_ENDPOINTS[endpoint_index]
    diagnostic = {
        "endpoint": endpoint,
        "status": "pending",
        "response_time": None,
        "error": None
    }
    try:
        start_time = time.time()
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1500
            },
            timeout=30
        )
        response_time = time.time() - start_time
        diagnostic["response_time"] = response_time

        if response.status_code == 200:
            diagnostic["status"] = "success"
            return response.json()["choices"][0]["message"]["content"], diagnostic
        else:
            diagnostic["status"] = "http_error"
            diagnostic["error"] = f"HTTP {response.status_code}: {response.text[:100]}"
            return None, diagnostic

    except requests.exceptions.Timeout:
        diagnostic["status"] = "timeout"
        diagnostic["error"] = "Délai dépassé"
        return None, diagnostic

    except Exception as e:
        diagnostic["status"] = "exception"
        diagnostic["error"] = str(e)
        return None, diagnostic

# Interface principale
st.set_page_config(page_title="Prospection Ametis", layout="centered")
st.title("🧐 Assistant Prospection Ametis")

# Authentification
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    password = st.text_input("Mot de passe", type="password")
    if st.button("Valider"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Accès refusé")
    st.stop()

# Zone de diagnostic
with st.expander("🔍 Diagnostic des endpoints API"):
    st.write("Test de connectivité aux endpoints DeepSeek:")
    results = []
    for endpoint in API_ENDPOINTS:
        status = "🟢 Actif" if test_endpoint(endpoint) else "🔴 Inactif"
        results.append(f"- [{endpoint}]({endpoint}): {status}")
    st.markdown("\n".join(results))
    st.info("Seuls les endpoints marqués comme 'Actif' seront utilisés")

# Saisie utilisateur
company = st.text_input("Nom de l'entreprise", "ACTIBIO 53")
sector = st.selectbox("Secteur", ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", "Industrie", "Autre"], index=0)

# Lancement génération
if st.button("Générer la fiche", type="primary"):
    if not company:
        st.warning("Veuillez saisir un nom d'entreprise")
    else:
        prompt = f"""
Vous êtes un assistant IA expert en prospection industrielle B2B.
Générez une fiche de synthèse pour l’entreprise suivante :
- Nom : {company}
- Secteur : {sector}

Incluez les sections suivantes :
1. Présentation synthétique de l’entreprise
2. Activités principales
3. Différenciation
4. Marché cible
5. Valeurs ou engagements
6. Responsables clés (qualité, production, technique, achats, marketing)

Soyez synthétique, précis et professionnel."
"""
        for i, endpoint in enumerate(API_ENDPOINTS):
            if test_endpoint(endpoint):
                st.info(f"🧠 Réflexion en cours, via : [{endpoint}]({endpoint})")
                progress = st.progress(0)
                for pct in range(1, 6):
                    time.sleep(0.15)
                    progress.progress(pct * 20)
                fiche, diag = call_deepseek_api(prompt, i)
                st.session_state.diagnostics = [diag]
                if fiche:
                    st.session_state.fiche = fiche
                    break
        else:
            st.error("❌ Aucun endpoint actif ou réponse invalide")

# Affichage fiche
if "fiche" in st.session_state:
    st.success("✅ Contenu reçu :")
    st.markdown(f"```markdown\n{st.session_state.fiche}\n```")
    st.download_button("📋 Copier la fiche", st.session_state.fiche, file_name="fiche.txt")

# Export PDF
if "fiche" in st.session_state:
    if st.button("📄 Exporter en PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in st.session_state.fiche.split('\n'):
            clean_line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 8, clean_line, ln=True)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, "rb") as f:
                st.download_button("📄 Télécharger PDF", f.read(), file_name=f"fiche_{company.replace(' ','_')}.pdf", mime="application/pdf")
