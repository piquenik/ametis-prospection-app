import streamlit as st
import requests
import os
import time
from datetime import datetime, timezone, timedelta
from fpdf import FPDF
import base64

# Configuration de la page
st.set_page_config(
    page_title="Assistant Prospection Ametis",
    layout="centered",
    page_icon="📊",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Style CSS optimisé
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
    @media (max-width: 640px) {
        .main-container {padding: 1rem;}
        .report-container {padding: 1rem;}
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
        'last_report': None
    }

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
    
    # Nettoyage des caractères
    def clean_text(text):
        return text.encode('latin-1', 'replace').decode('latin-1')
    
    # Contenu formaté
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
    
    # Pied de page
    pdf.set_y(-15)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, clean_text(f"Généré le {datetime.now(timezone(timedelta(hours=2))).strftime('%d/%m/%Y %H:%M')} par Assistant Prospection Ametis"), 0, 0, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

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
                tokens_used = result["usage"]["total_tokens"]
                
                # Mise à jour du journal
                french_tz = timezone(timedelta(hours=2))
                st.session_state.last_request = {
                    'date': datetime.now(french_tz).strftime("%Y-%m-%d %H:%M:%S"),
                    'entreprise': nom_entreprise,
                    'mode': "PRO" if recherche_pro else "Standard",
                    'tokens': tokens_used,
                    'last_report': content
                }
                
                # Affichage du résultat
                st.markdown("---")
                st.success("✅ Analyse terminée")
                
                with st.container():
                    st.markdown(
                        f'<div class="report-container">{content}</div>',
                        unsafe_allow_html=True
                    )
                
                # Export PDF amélioré
                if st.session_state.last_request['last_report']:
                    pdf_bytes = create_pdf(
                        nom_entreprise, 
                        secteur_cible, 
                        st.session_state.last_request['last_report']
                    )
                    
                    # Création du lien de téléchargement masqué
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="fiche_prospection_{nom_entreprise}.pdf" id="auto-download" style="visibility: hidden;"></a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # Bouton qui déclenche le téléchargement via JS
                    st.button(
                        "📄 Exporter en PDF",
                        key="export_btn",
                        help="Téléchargez la fiche complète au format PDF",
                        use_container_width=True
                    )
                    
                    # Script JS pour déclencher le téléchargement automatique
                    st.markdown("""
                    <script>
                    document.addEventListener('DOMContentLoaded', function() {
                        const downloadLink = document.getElementById('auto-download');
                        const exportBtn = document.querySelector('button[data-testid="baseButton-secondary"]');
                        
                        if (exportBtn && downloadLink) {
                            exportBtn.addEventListener('click', function() {
                                downloadLink.click();
                            });
                        }
                    });
                    </script>
                    """, unsafe_allow_html=True)
                
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
    
    st.markdown("---")
    st.subheader("Journal d'activité")
    st.write(f"**Dernière requête (UTC+2):** {st.session_state.last_request['date'] or 'Aucune'}")
    st.write(f"**Entreprise:** {st.session_state.last_request['entreprise'] or 'Aucune'}")
    st.write(f"**Mode:** {st.session_state.last_request['mode'] or 'Aucun'}")
    st.write(f"**Tokens utilisés:** {st.session_state.last_request['tokens'] or '0'}")
    
    if st.button("🔄 Réinitialiser"):
        st.session_state.clear()
        st.rerun()
