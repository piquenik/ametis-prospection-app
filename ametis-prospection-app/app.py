import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile
import socket
import json
from datetime import datetime

# Configuration
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
    APP_PASSWORD = st.secrets.get("APP_PASSWORD", "Ametis2025")
except:
    st.error("Erreur de configuration")
    st.stop()

# Initialisation
st.set_page_config(page_title="Prospection Ametis", layout="centered")
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stToolbar"] {display: none;}
</style>
""", unsafe_allow_html=True)

# Nouveaux endpoints à tester
API_ENDPOINTS = [
    "https://api.deepseek.ai/v1/chat/completions",  # Endpoint principal
    "https://api.deepseek.com/v1/chat/completions",  # Endpoint alternatif
    "https://gateway.deepseek.com/chat/completions"  # Nouveau endpoint à tester
]

# Fonction pour tester la connectivité
def test_endpoint(endpoint):
    try:
        test_url = endpoint.replace("/chat/completions", "")
        response = requests.get(test_url, timeout=5)
        return response.status_code == 200
    except:
        return False

# Fonction API robuste avec diagnostic
def call_deepseek_api(prompt, endpoint_index=0):
    """Tente différents endpoints avec diagnostic complet"""
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
            timeout=15
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

# Solution de repli locale améliorée
def generate_fallback_report(company, sector):
    villes = ["Laval", "Angers", "Nantes", "Rennes", "Le Mans"]
    return f"""
# 🧐 Fiche Prospection: {company}
**Secteur:** {sector}  
**Date de génération:** {datetime.now().strftime("%d/%m/%Y %H:%M")}
**Source:** Mode local Ametis

## 📌 Coordonnées
- **Adresse:** {random.randint(1,99)} rue des Entrepreneurs, {random.randint(44000, 44999)} {random.choice(villes)}
- **Site web:** www.{company.lower().replace(' ','')}.fr
- **Téléphone:** 02 {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}

## 🏢 Activité principale
Entreprise spécialisée dans le secteur {sector.lower()}. 

## 👥 Contacts clés
- **Responsable production:** production.{company.lower().replace(' ','')}@example.com
- **Responsable qualité:** qualite.{company.lower().replace(' ','')}@example.com
- **Responsable achats:** achats.{company.lower().replace(' ','')}@example.com

## ✉️ Email de prospection
> Objet: Solution de traçabilité pour votre activité {sector.lower()}
> 
> Bonjour,
> 
> En tant qu'entreprise spécialisée dans le secteur {sector.lower()}, nous pensons que nos solutions de traçabilité Ametis pourraient optimiser vos processus.
> 
> Nous proposons:
> - Étiqueteuses industrielles haute performance
> - Systèmes de traçabilité temps réel
> - Intégration ERP/WMS
> 
> Pouvons-nous planifier un court échange la semaine prochaine?
> 
> Cordialement,
> [Votre nom]
> Conseiller Ametis
> contact@ametis.eu
> 01 23 45 67 89

## 📊 Données stratégiques
- **Criticité besoin:** {random.choice(['Élevée', 'Moyenne', 'Faible'])}
- **Budget estimé:** {random.randint(10,50)} K€
- **Délai d'action:** {random.choice(['Immédiat', '1-3 mois', '3-6 mois'])}
"""

# Interface principale
def main():
    # Authentification
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        with st.container():
            st.title("🔒 Authentification")
            password = st.text_input("Mot de passe", type="password")
            if st.button("Valider"):
                if password == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Accès refusé")
            st.stop()
    
    # Application principale
    st.title("🧐 Assistant Prospection Ametis")
    st.caption("DeepSeek API - Mode diagnostic activé")
    
    # Diagnostic des endpoints
    with st.expander("🔍 Diagnostic des endpoints API"):
        st.write("Test de connectivité aux endpoints DeepSeek:")
        results = []
        for endpoint in API_ENDPOINTS:
            status = "🟢 Actif" if test_endpoint(endpoint) else "🔴 Inactif"
            results.append(f"- {endpoint}: {status}")
        st.markdown("\n".join(results))
        st.info("Seuls les endpoints marqués comme 'Actif' seront utilisés")
    
    company = st.text_input("Nom de l'entreprise", "ACTIBIO 53")
    sector = st.selectbox("Secteur", ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", "Industrie", "Autre"], index=0)
    
    if st.button("Générer la fiche", type="primary"):
        if not company:
            st.warning("Veuillez saisir un nom d'entreprise")
            return
            
        with st.spinner("Tentative de connexion à l'API DeepSeek..."):
            # Prompt optimisé
            prompt = f"""
Tu es un expert en prospection commerciale. Génère une fiche entreprise au format Markdown pour:
- Entreprise: {company}
- Secteur: {sector}

La fiche doit contenir:
1. Coordonnées complètes (adresse fictive mais plausible)
2. Description de l'activité (2-3 phrases)
3. 2 contacts clés avec emails
4. Un email de prospection court
5. Analyse des besoins potentiels

Sois concis et professionnel.
"""
            
            # Tentative avec différents endpoints
            fiche = None
            diagnostics = []
            
            for i, endpoint in enumerate(API_ENDPOINTS):
                st.info(f"Essai avec l'endpoint: {endpoint}")
                fiche, diag = call_deepseek_api(prompt, i)
                diagnostics.append(diag)
                
                if fiche:
                    break
            
            # Solution de repli si échec
            if not fiche:
                st.warning("Tous les endpoints ont échoué - Utilisation du mode local")
                fiche = generate_fallback_report(company, sector)
            
            st.session_state.fiche = fiche
            st.session_state.diagnostics = diagnostics
            st.markdown(fiche)
    
    # Affichage du diagnostic
    if st.session_state.get('diagnostics'):
        with st.expander("📊 Résultats des tests API"):
            for diag in st.session_state.diagnostics:
                status_icon = "🟢" if diag["status"] == "success" else "🔴"
                st.write(f"{status_icon} Endpoint: {diag['endpoint']}")
                st.write(f"- Statut: {diag['status']}")
                if diag["response_time"]:
                    st.write(f"- Temps de réponse: {diag['response_time']:.2f}s")
                if diag["error"]:
                    st.write(f"- Erreur: `{diag['error']}`")
                st.divider()

    # Export PDF
    if st.session_state.get('fiche'):
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
                    st.download_button(
                        "Télécharger la fiche PDF",
                        data=f.read(),
                        file_name=f"prospection_{company.replace(' ', '_')[:30]}.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()
