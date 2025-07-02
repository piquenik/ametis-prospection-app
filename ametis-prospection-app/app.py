import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile
import random
from datetime import datetime

# Configuration des endpoints valides
API_ENDPOINTS = [
    "https://api.deepseek.com/v1/chat/completions",
    "https://gateway.deepseek.com/chat/completions"
]

# Fonction de test POST d'un endpoint
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

# Appel DeepSeek API
def call_deepseek_api(prompt, endpoint, api_key):
    try:
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 1500
            },
            timeout=15
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"], "success"
        else:
            return None, f"Erreur HTTP {response.status_code}"
    except Exception as e:
        return None, str(e)

# Fallback local
def generate_fallback_report(company, sector):
    villes = ["Laval", "Angers", "Nantes", "Rennes", "Le Mans"]
    return f"""
# 🧐 Fiche Prospection: {company}
**Secteur:** {sector}  
**Date de génération:** {datetime.now().strftime("%d/%m/%Y %H:%M")}  
**Source:** Mode local Ametis

## 📌 Coordonnées
- **Adresse:** {random.randint(1,99)} rue des Entrepreneurs, {random.randint(44000,44999)} {random.choice(villes)}
- **Site web:** www.{company.lower().replace(' ','')}.fr
- **Téléphone:** 02 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}

## 🏢 Activité principale
Entreprise spécialisée dans le secteur {sector.lower()}.

## 👥 Contacts clés
- **Responsable production:** production.{company.lower().replace(' ','')}@example.com
- **Responsable qualité:** qualite.{company.lower().replace(' ','')}@example.com

## ✉️ Email de prospection
> Bonjour,
>
> En tant qu'entreprise du secteur {sector.lower()}, nos solutions de traçabilité industrielles peuvent optimiser vos flux.
> - Étiquetage automatisé
> - Traçabilité temps réel
> - Intégration ERP/WMS
>
> Seriez-vous disponible pour un échange rapide ?
>
> Cordialement,  
> [Votre nom] – Ametis  
> contact@ametis.eu | 01 23 45 67 89

## 📊 Données stratégiques
- **Criticité besoin:** {random.choice(['Élevée', 'Moyenne', 'Faible'])}
- **Budget estimé:** {random.randint(10,50)} K€
- **Délai d'action:** {random.choice(['Immédiat', '1-3 mois', '3-6 mois'])}
"""

# Interface principale
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
        prompt = f"""
Tu es un expert en prospection commerciale. Génère une fiche entreprise au format Markdown pour:
- Entreprise: {company}
- Secteur: {sector}

La fiche doit contenir:
1. Coordonnées complètes (adresse fictive mais plausible)
2. Description de l'activité
3. Contacts clés (emails)
4. Email de prospection
5. Analyse des besoins

Sois synthétique et professionnel.
"""
        fiche = None
        for endpoint in API_ENDPOINTS:
            if test_endpoint(endpoint, api_key):
                fiche, status = call_deepseek_api(prompt, endpoint, api_key)
                if fiche:
                    break

        if not fiche:
            st.warning("Tous les endpoints ont échoué - utilisation du mode local")
            fiche = generate_fallback_report(company, sector)

        st.session_state.fiche = fiche
        st.markdown(fiche)

    if st.session_state.get("fiche"):
        if st.button("📄 Exporter en PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in st.session_state.fiche.split('\n'):
                pdf.cell(0, 8, line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                pdf.output(tmp.name)
                with open(tmp.name, "rb") as f:
                    st.download_button(
                        "Télécharger la fiche PDF",
                        data=f.read(),
                        file_name=f"fiche_{company.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )

    with st.expander("🧪 Test direct DeepSeek API (POST réel)"):
        test_prompt = st.text_area("Prompt de test", "Donne-moi un résumé de l'entreprise ACTIBIO 53.")
        test_endpoint_url = st.selectbox("Endpoint", API_ENDPOINTS)
        if st.button("Lancer le test manuel"):
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                response = requests.post(
                    test_endpoint_url,
                    headers=headers,
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": test_prompt}],
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    timeout=15
                )
                st.write(f"Code HTTP : {response.status_code}")
                if response.status_code == 200:
                    st.markdown(response.json()["choices"][0]["message"]["content"])
                else:
                    st.code(response.text[:1000])
            except Exception as e:
                st.error(str(e))

if __name__ == "__main__":
    main()
    
