import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile
from datetime import datetime

API_ENDPOINTS = [
    "https://api.deepseek.com/v1/chat/completions",
    "https://gateway.deepseek.com/chat/completions"
]

def test_endpoint(endpoint, api_key):
    try:
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "ping"}],
                "temperature": 0.1,
                "max_tokens": 10
            },
            timeout=8
        )
        return response.status_code in [200, 401]
    except:
        return False

def main():
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]
        app_password = st.secrets.get("APP_PASSWORD", "Ametis2025")
    except:
        st.error("Erreur de configuration des secrets")
        st.stop()

    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.title("🔒 Authentification")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Valider"):
            if password == app_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
        st.stop()

    st.title("😮 Assistant Prospection Ametis")

    with st.expander("🔍 Diagnostic des endpoints API"):
        st.write("Test de connectivité aux endpoints DeepSeek:")
        results = []
        for endpoint in API_ENDPOINTS:
            actif = test_endpoint(endpoint, api_key)
            status = "🟢 Actif" if actif else "🔴 Inactif"
            results.append(f"- [{endpoint}]({endpoint}): {status}")
        st.markdown("\n".join(results))
        st.info("Seuls les endpoints marqués comme 'Actif' seront utilisés")

    company = st.text_input("Nom de l'entreprise", "ACTIBIO 53")
    sector = st.selectbox("Secteur", ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", "Industrie", "Autre"])

    if st.button("Générer la fiche", type="primary"):
        prompt = f"Résumé synthétique pour l’entreprise {company}, secteur {sector}"
        endpoint = API_ENDPOINTS[0]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 800
        }

        st.info(f"🧠 Réflexion en cours, via : {endpoint}")
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=20)
            result = response.json()
            if "choices" in result and result["choices"]:
                content = result["choices"][0]["message"]["content"]
                st.session_state.fiche = content
                st.success("✅ Contenu reçu :")
                st.markdown(content)
            else:
                st.warning("Réponse sans contenu exploitable.")
                st.code(response.text[:1000])
        except Exception as e:
            st.error(f"❌ Exception levée : {e}")

    if st.session_state.get("fiche"):
        st.markdown("---")
        st.markdown("### 📄 Fiche générée")
        st.markdown(st.session_state.fiche)

        st.download_button(
            "📋 Copier la fiche (texte)",
            data=st.session_state.fiche,
            file_name="fiche_prospection.txt"
        )

        if st.button("📥 Télécharger en PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in st.session_state.fiche.split("\n"):
                pdf.cell(0, 10, line.encode("latin-1", "replace").decode("latin-1"), ln=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button(
                        "📄 Télécharger le PDF",
                        data=f.read(),
                        file_name=f"fiche_{company.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()

