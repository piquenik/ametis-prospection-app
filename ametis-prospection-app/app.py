import streamlit as st
import requests
import os
import time
import json
import csv
import sqlite3
from datetime import datetime, timezone, timedelta
from fpdf import FPDF

# Configuration de la page
st.set_page_config(
    page_title="Assistant Prospection Ametis VBeta V1,1DS",
    layout="wide",
    page_icon="🤖",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Fichiers de config
USER_FILE = "users.json"
DB_FILE = "persistent_logs.db"

# Initialisation de la base de données
def init_database():
    """Initialise la base de données SQLite pour les logs persistants"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Créer la table des logs si elle n'existe pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS global_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            user TEXT NOT NULL,
            entreprise TEXT NOT NULL,
            secteur TEXT NOT NULL,
            mode TEXT NOT NULL,
            tokens INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Fonction pour ajouter un log
def add_log_entry(datetime_str, user, entreprise, secteur, mode, tokens):
    """Ajoute une entrée dans les logs persistants"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO global_logs (datetime, user, entreprise, secteur, mode, tokens)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime_str, user, entreprise, secteur, mode, tokens))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'ajout du log: {e}")
        return False

# Fonction pour récupérer les logs
def get_logs(limit=100):
    """Récupère les logs depuis la base de données"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT datetime, user, entreprise, secteur, mode, tokens
            FROM global_logs
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        logs = cursor.fetchall()
        conn.close()
        
        # Convertir en format dictionnaire pour compatibilité
        return [
            {
                "datetime": log[0],
                "user": log[1],
                "entreprise": log[2],
                "secteur": log[3],
                "mode": log[4],
                "tokens": log[5]
            }
            for log in logs
        ]
    except Exception as e:
        st.error(f"Erreur lors de la récupération des logs: {e}")
        return []

# Fonction pour nettoyer les anciens logs (optionnel)
def cleanup_old_logs(days_to_keep=30):
    """Supprime les logs plus anciens que X jours"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cursor.execute('''
            DELETE FROM global_logs 
            WHERE created_at < ?
        ''', (cutoff_date,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erreur lors du nettoyage des logs: {e}")

# Initialiser la base de données au démarrage
init_database()

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

    /* Styles pour les boutons de fonctionnalités */
    .feature-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    .feature-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }

    @media (max-width: 640px) {
        .main-container {padding: 1rem;}
        .report-container {padding: 1rem;}
    }
</style>
""", unsafe_allow_html=True)

# Layout principal avec colonnes
col_main, col_features = st.columns([2, 1])

with col_main:
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

# Fonctions pour les requêtes API
def make_api_request(payload, timeout=60):
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=timeout
        )
        
        # Debug: afficher le code de statut
        if response.status_code != 200:
            st.error(f"Erreur API - Code: {response.status_code}")
            st.error(f"Réponse: {response.text}")
            
        return response
    except requests.exceptions.Timeout:
        st.error("Timeout - La requête a pris trop de temps")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Erreur de connexion à l'API DeepSeek")
        return None
    except Exception as e:
        st.error(f"Erreur lors de la requête API: {e}")
        return None

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

def generate_competitors_prompt(entreprise, secteur):
    return f"""Identifie et liste 10 entreprises concurrentes ou similaires à {entreprise} dans le secteur {secteur}.

Pour chaque entreprise, fournis :
- Nom complet
- Ville/Région
- Secteur précis
- Taille approximative (CA ou effectifs)
- Particularité/spécialité

Localisation prioritaire : dans un rayon de 50km autour de {entreprise}."""

def generate_prospects_prompt(entreprise, secteur):
    return f"""Suggère 10 entreprises prospects potentiels pour {entreprise} (secteur: {secteur}).

Critères de sélection :
- Entreprises qui pourraient avoir besoin des services/produits de {entreprise}
- Localisation : rayon de 50km autour de {entreprise}
- Secteurs complémentaires ou clients potentiels
- Taille compatible pour partenariat

Pour chaque prospect :
- Nom et localisation
- Secteur d'activité
- Pourquoi c'est un prospect intéressant
- Contact suggéré (fonction)"""

def generate_market_analysis_prompt(entreprise, secteur):
    return f"""Analyse le marché local pour {entreprise} dans le secteur {secteur}.

Analyse :
1. **Tendances du marché** (croissance, défis, opportunités)
2. **Concurrence locale** (3-5 acteurs principaux)
3. **Opportunités de développement**
4. **Risques et menaces**
5. **Recommandations stratégiques**

Focus géographique : région de {entreprise}."""

def generate_contacts_prompt(entreprise, secteur):
    return f"""Recherche des contacts clés pour {entreprise} dans le secteur {secteur}.

Types de contacts recherchés :
1. **Direction** (PDG, DG, Directeurs)
2. **Commercial** (Directeur commercial, responsables ventes)
3. **Technique** (CTO, Directeur technique, ingénieurs)
4. **Partenaires** (distributeurs, fournisseurs locaux)
5. **Institutionnels** (organismes professionnels, clusters)

Pour chaque contact : nom, fonction, coordonnées si disponibles."""

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
def create_pdf(entreprise, secteur, contenu, type_analyse="Standard"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # En-tête
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Analyse {type_analyse}: {entreprise}", ln=1, align='C')
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

# Fonction pour exécuter une analyse supplémentaire
def execute_additional_analysis(prompt, analysis_type, use_pro_model=True):
    if not st.session_state.last_request['last_report']:
        st.error("Aucune recherche précédente trouvée. Effectuez d'abord une recherche standard.")
        return
    
    # Utilisation d'un container dans la colonne principale pour afficher les résultats
    with col_main:
        loading_placeholder = st.empty()
        loading_placeholder.markdown(f"""
        <div class="loading-container">
            <div class="loading-logo">🔍</div>
            <h3 class="loading-text">Analyse {analysis_type}</h3>
            <p>Traitement en cours...</p>
        </div>
        """, unsafe_allow_html=True)

        payload = {
            "model": "deepseek-reasoner" if use_pro_model else "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Expert en analyse B2B et prospection commerciale"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1500,
            "web_search": True
        }

        try:
            response = make_api_request(payload, timeout=120)
            loading_placeholder.empty()
            
            if response and response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                tokens_used = result["usage"]["total_tokens"]
                
                # Affichage du résultat dans la colonne principale
                st.markdown("---")
                st.success(f"✅ Analyse {analysis_type} terminée")
                
                with st.container():
                    st.markdown(
                        f'<div class="report-container">{content}</div>',
                        unsafe_allow_html=True
                    )
                
                # Génération du PDF pour l'analyse supplémentaire
                try:
                    pdf_bytes = create_pdf(
                        st.session_state.last_request['entreprise'], 
                        "Analyse", 
                        content, 
                        analysis_type
                    )
                    
                    st.download_button(
                        label=f"📄 Exporter {analysis_type} en PDF",
                        data=pdf_bytes,
                        file_name=f"{analysis_type}_{st.session_state.last_request['entreprise']}.pdf",
                        mime="application/pdf",
                        key=f"pdf_{analysis_type}_{int(time.time())}",
                        use_container_width=True
                    )
                except Exception as pdf_error:
                    st.warning(f"Erreur génération PDF: {pdf_error}")
                
                return content
            else:
                error_msg = f"Erreur API: {response.status_code}"
                if response:
                    try:
                        error_detail = response.json()
                        error_msg += f" - {error_detail.get('error', {}).get('message', 'Erreur inconnue')}"
                    except:
                        error_msg += f" - {response.text}"
                st.error(error_msg)
                
        except Exception as e:
            loading_placeholder.empty()
            st.error(f"Erreur lors de l'analyse {analysis_type}: {str(e)}")
            st.error(f"Détails: {type(e).__name__}")
            
            # Debug info
            st.write("Debug - Payload envoyé:")
            st.json(payload)

# Traitement de la recherche avec animation
with col_main:
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

            response = make_api_request(payload, timeout=120 if recherche_pro else 60)
            loading_placeholder.empty()

            if response and response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                tokens_used = result["usage"]["total_tokens"]

                # Génération du PDF
                pdf_bytes = create_pdf(nom_entreprise, secteur_cible, content)

                # Mise à jour du journal
                french_tz = timezone(timedelta(hours=2))
                current_datetime = datetime.now(french_tz).strftime("%Y-%m-%d %H:%M:%S")
                
                st.session_state.last_request = {
                    'date': current_datetime,
                    'entreprise': nom_entreprise,
                    'mode': "PRO" if recherche_pro else "Standard",
                    'tokens': tokens_used,
                    'last_report': content,
                    'pdf_bytes': pdf_bytes
                }

                st.session_state.history.append({
                    'date': current_datetime,
                    'entreprise': nom_entreprise,
                    'mode': "PRO" if recherche_pro else "Standard",
                    'tokens': tokens_used,
                    'content': content,
                    'pdf_bytes': pdf_bytes
                })

                st.session_state.history = st.session_state.history[-10:]

                # Log persistant avec SQLite
                success = add_log_entry(
                    current_datetime,
                    st.session_state.current_user,
                    nom_entreprise,
                    secteur_cible,
                    "PRO" if recherche_pro else "Standard",
                    tokens_used
                )
                
                if success:
                    st.success("✅ Recherche enregistrée de manière persistante")
                else:
                    st.warning("⚠️ Recherche effectuée mais erreur d'enregistrement")

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
                st.error(f"Erreur API: {response.status_code if response else 'Pas de réponse'}")

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

                suivi_response = make_api_request(suivi_payload, timeout=120)
                if suivi_response and suivi_response.status_code == 200:
                    suivi_content = suivi_response.json()["choices"][0]["message"]["content"]
                    st.markdown("---")
                    st.subheader("🧠 Réponse à la question de suivi")
                    st.markdown(f'<div class="report-container">{suivi_content}</div>', unsafe_allow_html=True)
                else:
                    st.error(f"Erreur API Deepseek: {suivi_response.status_code if suivi_response else 'Pas de réponse'}")

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

# Colonne des fonctionnalités supplémentaires (VERSION SIMPLIFIÉE)
with col_features:
    st.markdown("### 🚀 Fonctionnalités Avancées")
    
    # Vérifier si une recherche a été effectuée
    if st.session_state.last_request['last_report']:
        entreprise_actuelle = st.session_state.last_request['entreprise']
        st.markdown(f"**Entreprise analysée:** {entreprise_actuelle}")
        
        # Boutons directs sans les bulles
        if st.button("🏢 Identifier les Concurrents (50km)", key="competitors", use_container_width=True):
            prompt = generate_competitors_prompt(entreprise_actuelle, "Analyse concurrentielle")
            execute_additional_analysis(prompt, "Concurrents", use_pro_model=False)
        
        if st.button("🎯 Suggérer des Prospects (50km)", key="prospects", use_container_width=True):
            prompt = generate_prospects_prompt(entreprise_actuelle, "Prospection")
            execute_additional_analysis(prompt, "Prospects", use_pro_model=False)
        
        if st.button("📈 Analyser le Marché Local", key="market", use_container_width=True):
            prompt = generate_market_analysis_prompt(entreprise_actuelle, "Marché")
            execute_additional_analysis(prompt, "Marché", use_pro_model=False)
        
        if st.button("👥 Rechercher des Contacts Clés", key="contacts", use_container_width=True):
            prompt = generate_contacts_prompt(entreprise_actuelle, "Contacts")
            execute_additional_analysis(prompt, "Contacts", use_pro_model=False)
        
        # Section Analyse Personnalisée
        st.markdown("---")
        st.markdown("**🔧 Analyse Personnalisée**")
        
        custom_prompt = st.text_area("Votre demande personnalisée:", key="custom_analysis", height=100)
        if st.button("🚀 Analyser", key="custom", use_container_width=True) and custom_prompt:
            full_prompt = f"""Analyse personnalisée pour {entreprise_actuelle}:

{custom_prompt}

Basé sur les informations disponibles sur cette entreprise, fournis une analyse détaillée et actionnable."""
            execute_additional_analysis(full_prompt, "Personnalisée", use_pro_model=False)
    
    else:
        st.info("🔍 Effectuez d'abord une recherche pour débloquer les fonctionnalités avancées")
        st.markdown("""
        **Fonctionnalités disponibles après recherche:**
        - 🏢 Analyse concurrentielle
        - 🎯 Suggestion de prospects
        - 📈 Analyse du marché local
        - 👥 Recherche de contacts
        - 🔧 Analyse personnalisée
        """)

# Sidebar historique (déplacée en bas)
with st.sidebar:
    st.info("""
    **Instructions:**
    1. Renseignez le nom de l'entreprise
    2. Sélectionnez le secteur
    3. Lancez la recherche
    4. Utilisez les fonctionnalités avancées →
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

# Zone admin avec logs persistants
if st.session_state.role == "admin":
    st.markdown("---")
    st.subheader("🔒 Journal des Recherches Persistant (admin)")
    
    # Bouton pour nettoyer les anciens logs
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧹 Nettoyer logs > 30 jours"):
            cleanup_old_logs(30)
            st.success("Logs anciens supprimés")
    
    with col2:
        # Afficher le nombre total de logs
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM global_logs")
            total_logs = cursor.fetchone()[0]
            conn.close()
            st.info(f"📊 Total des logs: {total_logs}")
        except Exception as e:
            st.error(f"Erreur comptage logs: {e}")
    
    try:
        # Récupération des logs depuis SQLite
        log_data = get_logs(100)  # Derniers 100 logs
        
        if log_data:
            # Affichage sous forme de dataframe
            import pandas as pd
            df = pd.DataFrame(log_data)
            st.dataframe(df, use_container_width=True)

            # Génération CSV depuis SQLite
            csv_data = "datetime,user,entreprise,secteur,mode,tokens\n" + "\n".join(
                f"{r['datetime']},{r['user']},{r['entreprise']},{r['secteur']},{r['mode']},{r['tokens']}"
                for r in log_data
            )

            st.download_button(
                label="📃 Télécharger CSV (Logs Persistants)",
                data=csv_data,
                file_name=f"journal_recherches_persistant_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key=f"csv_persistent_{datetime.now().isoformat()}",
                use_container_width=True
            )
            
            # Statistiques rapides
            st.markdown("### 📈 Statistiques")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_requests = len(log_data)
                st.metric("Total requêtes", total_requests)
            
            with col2:
                if log_data:
                    total_tokens = sum(r['tokens'] for r in log_data)
                    st.metric("Total tokens", f"{total_tokens:,}")
                else:
                    st.metric("Total tokens", 0)
            
            with col3:
                if log_data:
                    unique_users = len(set(r['user'] for r in log_data))
                    st.metric("Utilisateurs actifs", unique_users)
                else:
                    st.metric("Utilisateurs actifs", 0)
        else:
            st.info("Aucune donnée persistante enregistrée.")
    except Exception as e:
        st.error(f"Erreur chargement journal persistant: {e}")
        
    # Options avancées pour admin
    with st.expander("🔧 Options Avancées Admin"):
        st.markdown("**Gestion de la base de données:**")
        
        if st.button("🗑️ Vider complètement les logs", type="secondary"):
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM global_logs")
                conn.commit()
                conn.close()
                st.success("Tous les logs ont été supprimés")
            except Exception as e:
                st.error(f"Erreur suppression: {e}")
        
        st.markdown("**Export de sauvegarde:**")
        if st.button("💾 Exporter sauvegarde complète"):
            try:
                all_logs = get_logs(10000)  # Tous les logs
                backup_data = {
                    "export_date": datetime.now().isoformat(),
                    "total_logs": len(all_logs),
                    "logs": all_logs
                }
                backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
                
                st.download_button(
                    label="💾 Télécharger sauvegarde JSON",
                    data=backup_json,
                    file_name=f"backup_logs_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    key="backup_download"
                )
            except Exception as e:
                st.error(f"Erreur export: {e}")

# Message de statut persistance
st.markdown("---")
st.info("💾 **Logs persistants activés** - Vos données sont conservées même après redémarrage de l'application")
