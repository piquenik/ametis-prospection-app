import streamlit as st
import requests
import os
import time
import json
import csv
from datetime import datetime, timezone, timedelta
from fpdf import FPDF

# Configuration de la page
st.set_page_config(
    page_title="Assistant Prospection Ametis VBeta V1,1DS",
    layout="centered",
    page_icon="🤖",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Fichiers de config
USER_FILE = "users.json"
LOG_FILE = "global_log.json"

@st.cache_data
def load_users():
    if not os.path.exists(USER_FILE):
        st.error(f"Fichier {USER_FILE} introuvable. Veuillez le créer à la racine de l'application.")
        st.stop()
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

users = load_users()

# Authentification utilisateur
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.role = None

if not st.session_state.authenticated:
    st.title("🔐 Connexion Utilisateur Ametis")
    login = st.text_input("Identifiant exemple 'Nicolas Piquet = (NPI)")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        for user in users:
            if user["username"] == login and user["password"] == password:
                st.session_state.authenticated = True
                st.session_state.current_user = login
                st.session_state.role = user.get("role", "user")
                st.success("Connexion réussie")
                st.rerun()
        else:
            st.error("Identifiant ou mot de passe incorrect")
    st.stop()

# Style CSS avec animation
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main-container {
        max-width: 900px;
        padding: 2rem;
        margin: 0 auto;
    }
    .report-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 2rem;
        margin-top: 1rem;
        word-wrap: break-word;
    }

    /* Animation de chargement */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }

    .loading-container {
        text-align: center;
        margin: 2rem 0;
        padding: 2rem;
        border-radius: 10px;
        background-color: #f0f2f6;
    }

    .loading-logo {
        font-size: 2.5rem;
        animation: pulse 2s infinite;
        margin-bottom: 1rem;
    }

    .loading-text {
        color: #4b8bff;
        font-weight: bold;
        margin-top: 1rem;
    }

    @media (max-width: 640px) {
        .main-container {padding: 1rem;}
        .report-container {padding: 1rem;}
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title(" 🔍 ASSISTANT Prospection Ametis")
st.markdown(f"-VBeta 1,1DeepSeek | Connecté en tant que: **{st.session_state.current_user}** ({st.session_state.role})")

# Paramètres
with st.expander("⚙️ Paramètres avancés", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider("Niveau de précision", 0.1, 1.0, 0.6)
    with col2:
        max_tokens = st.slider("Longueur de réponse", 500, 2000, 1200)

# Formulaire de recherche
with st.form("recherche_form"):
    nom_entreprise = st.text_input("Nom de l'entreprise (Nom + Dep + Ville ex: Actibio 53 changé)*")
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

# Journal d'activité
if 'last_request' not in st.session_state:
    st.session_state.last_request = {
        'date': None,
        'entreprise': None,
        'mode': None,
        'tokens': None,
        'last_report': None,
        'pdf_bytes': None
    }

if 'history' not in st.session_state:
    st.session_state.history = []

# Fonction de création du PDF
def create_pdf(entreprise, secteur, contenu):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # En-tête
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Fiche Prospection: {entreprise}", ln=1, align='C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(200, 10, txt=f"Secteur: {secteur}", ln=1, align='C')
    pdf.ln(10)

    def clean_text(text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", size=10)
    lines = contenu.split('\n')
    for line in lines:
        clean_line = clean_text(line)
        if clean_line.startswith('### '):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(200, 8, txt=clean_line[4:].strip(), ln=1)
            pdf.set_font('Arial', '', 10)
        elif clean_line.startswith('- '):
            pdf.cell(10)
            pdf.cell(200, 8, txt='- ' + clean_line[2:].strip(), ln=1)
        else:
            pdf.multi_cell(0, 8, txt=clean_line.strip())
        pdf.ln(2)

    pdf.set_y(-15)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, clean_text(f"Généré le {datetime.now(timezone(timedelta(hours=2))).strftime('%d/%m/%Y %H:%M')} par Assistant Prospection Ametis"), 0, 0, 'C')

    return pdf.output(dest='S').encode('latin-1')

# Traitement de la recherche avec animation
if recherche_standard or recherche_pro:
    loading_placeholder = st.empty()
    loading_placeholder.markdown("""
    <div class="loading-container">
        <div class="loading-logo">🔍</div>
        <h3 class="loading-text">Ametis Prospect+</h3>
        <p>Notre équipe analyse les données...</p>
        <div style="font-size: 1.5rem;">
            <span style="animation: pulse 2s infinite;">🤖</span>
            <span style="animation: pulse 2s infinite 0.5s;">📊</span>
            <span style="animation: pulse 2s infinite 1s;">💼</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

            # Effacer l'animation
            loading_placeholder.empty()

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                tokens_used = result["usage"]["total_tokens"]

                # Génération du PDF
                pdf_bytes = create_pdf(nom_entreprise, secteur_cible, content)

                # Mise à jour du journal
                french_tz = timezone(timedelta(hours=2))
                st.session_state.last_request = {
                    'date': datetime.now(french_tz).strftime("%Y-%m-%d %H:%M:%S"),
                    'entreprise': nom_entreprise,
                    'mode': "PRO" if recherche_pro else "Standard",
                    'tokens': tokens_used,
                    'last_report': content,
                    'pdf_bytes': pdf_bytes
                }

                st.session_state.history.append({
                    'date': st.session_state.last_request['date'],
                    'entreprise': nom_entreprise,
                    'mode': "PRO" if recherche_pro else "Standard",
                    'tokens': tokens_used,
                    'content': content,
                    'pdf_bytes': pdf_bytes
                })

                st.session_state.history = st.session_state.history[-10:]

                # Log global admin
                try:
                    log_entry = {
                        "datetime": st.session_state.last_request['date'],
                        "user": st.session_state.current_user,
                        "entreprise": nom_entreprise,
                        "secteur": secteur_cible,
                        "mode": st.session_state.last_request['mode'],
                        "tokens": tokens_used
                    }
                    if os.path.exists(LOG_FILE):
                        with open(LOG_FILE, "r", encoding="utf-8") as f:
                            logs = json.load(f)
                    else:
                        logs = []
                    logs.append(log_entry)
                    with open(LOG_FILE, "w", encoding="utf-8") as f:
                        json.dump(logs[-100:], f, indent=2)
                except Exception as e:
                    st.warning(f"Erreur journalisation: {e}")

                # Affichage du résultat
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
            loading_placeholder.empty()
            st.error(f"Erreur: {str(e)}")

# Bouton d'export PDF
if st.session_state.last_request['last_report']:
    st.download_button(
        label="📄 Exporter en PDF",
        data=st.session_state.last_request['pdf_bytes'],
        file_name=f"fiche_prospection_{st.session_state.last_request['entreprise']}.pdf",
        mime="application/pdf",
        key=f"pdf_{st.session_state.last_request['entreprise']}_{st.session_state.last_request['date']}",
        help="Télécharger la fiche au format PDF",
        use_container_width=True
    )

    # Champ de question de suivi
    st.markdown("---")
    st.subheader("🔁 Question de suivi (mode Raisonnement avec sources)")
    question_suivi = st.text_input("Posez une question de suivi sur cette entreprise :")

        # Bouton suggestion tournée
    if st.button("🗺️ Proposer une tournée de prospection (50 km)", key="suggest_tournee"):
        st.session_state.suivi_q = (
            "Établis une tournée de prospection dans un rayon de 50 km autour de l'adresse de l'entreprise mentionnée. "
            "Propose un tableau avec 10 entreprises similaires ou complémentaires, incluant :\n"
            "- Nom de l'entreprise\n- Adresse complète\n- Distance estimée (en km) par rapport à l'entreprise cible\n"
            "Classe-les par proximité. Si possible, choisis des entreprises du même secteur ou susceptibles d'être intéressées par nos solutions de marquage industriel."
        )
        st.rerun()

    if suivi_question or 'suivi_q' in st.session_state:
        question = suivi_question or st.session_state.get('suivi_q', '')
        with st.spinner("Raisonnement en cours..."):
            payload = {
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "system", "content": "Expert en analyse B2B"},
                    {"role": "user", "content": st.session_state.last_request['last_report']},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.6,
                "max_tokens": 1500,
                "web_search": True
            }
            try:
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
                    json=payload,
                    timeout=180
                )
                if response.status_code == 200:
                    result = response.json()
                    followup = result["choices"][0]["message"]["content"]
                    st.markdown("---")
                    st.markdown(
                        f'<div class="report-container"><div style="text-align:right;font-size:0.9rem;color:#888">🧠 RAISONNEMENT 🌐</div>{followup}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.error("Erreur de réponse")
            except Exception as e:
                st.error(f"Erreur traitement: {e}")
...

    if question_suivi:
        with st.spinner("Analyse complémentaire en cours..."):
            suivi_payload = {
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "system", "content": "Expert en analyse B2B"},
                    {"role": "user", "content": st.session_state.last_request['last_report']},
                    {"role": "user", "content": question_suivi}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "web_search": True
            }

            try:
                suivi_response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"},
                    json=suivi_payload,
                    timeout=120
                )
                if suivi_response.status_code == 200:
                    suivi_content = suivi_response.json()["choices"][0]["message"]["content"]
                    st.markdown("---")
                    st.subheader("🧠 Réponse à la question de suivi")
                    st.markdown(f'<div class="report-container">{suivi_content}</div>', unsafe_allow_html=True)
                else:
                    st.error(f"Erreur API Deepseek: {suivi_response.status_code}")
            except Exception as err:
                st.error(f"Erreur lors de la question de suivi: {err}")

    # Bouton Nouvelle recherche
    if st.button("🔁 Nouvelle recherche"):
        st.session_state.last_request = {
            'date': None,
            'entreprise': None,
            'mode': None,
            'tokens': None,
            'last_report': None,
            'pdf_bytes': None
        }
        st.rerun()

# Sidebar
with st.sidebar:
    st.info("""
    **Instructions:**
    1. Renseignez le nom de l'entreprise
    2. Sélectionnez le secteur
    3. Lancez la recherche
    4. Posez des questions Supplementaires
    """)

    st.markdown("---")
    st.subheader("🕒 Historique des 10 dernières requêtes")

    if st.session_state.history:
        for i, req in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{req['entreprise']} ({req['mode']}) - {req['date']}", expanded=False):
                if st.button("🔁 Recharger cette fiche", key=f"reload_{i}"):
                    st.session_state.last_request = {
                        'date': req['date'],
                        'entreprise': req['entreprise'],
                        'mode': req['mode'],
                        'tokens': req['tokens'],
                        'last_report': req['content'],
                        'pdf_bytes': req['pdf_bytes']
                    }
                    st.rerun()
    else:
        st.write("Aucune requête enregistrée.")

    st.markdown("---")
    if st.button("🔄 Réinitialiser session"):
        st.session_state.clear()
        st.rerun()

# Zone admin
if st.session_state.role == "admin":
    st.markdown("---")
    st.subheader("🔒 Journal des Recherches (admin)")
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                log_data = json.load(f)
            if log_data:
                st.dataframe(log_data[::-1])

                # Génération CSV
                csv_data = "datetime,user,entreprise,secteur,mode,tokens\n" + "\n".join(
                    f"{r['datetime']},{r['user']},{r['entreprise']},{r['secteur']},{r['mode']},{r['tokens']}"
                    for r in log_data
                )

                # Téléchargement sans rechargement de page
                st.download_button(
                    label="📃 Télécharger CSV",
                    data=csv_data,
                    file_name="journal_recherches.csv",
                    mime="text/csv",
                    key=f"csv_{datetime.now().isoformat()}",
                    use_container_width=True
                )
            else:
                st.info("Aucune donnée enregistrée.")
        else:
            st.info("Journal non encore créé.")
    except Exception as e:
        st.error(f"Erreur chargement journal: {e}")
