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
    page_icon="📊"
)

# Style CSS personnalisé
st.markdown("""
<style>
    /* ... (conserver le style existant) ... */
    .export-btn {
        margin-top: 1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ... (conserver tout le code existant jusqu'à l'affichage des résultats) ...

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
                    'last_report': content  # Stocker le contenu pour export
                }
                
                # Affichage du résultat
                st.markdown("---")
                st.success("✅ Analyse terminée")
                
                with st.container():
                    st.markdown(
                        f'<div class="report-container">{content}</div>',
                        unsafe_allow_html=True
                    )
                
                # Bouton d'export PDF
                if st.session_state.last_request['last_report']:
                    pdf_bytes = create_pdf(
                        nom_entreprise, 
                        secteur_cible, 
                        st.session_state.last_request['last_report']
                    )
                    
                    st.download_button(
                        label="📄 Exporter en PDF",
                        data=pdf_bytes,
                        file_name=f"fiche_prospection_{nom_entreprise}.pdf",
                        mime="application/pdf",
                        key="export_pdf",
                        use_container_width=True,
                        help="Génère un PDF de la fiche de prospection",
                        type="primary",
                        on_click=lambda: st.toast(f"PDF généré pour {nom_entreprise}!")
                    )
                
                if recherche_pro:
                    st.info("🌐 Recherche web activée | Mode approfondi")

# ... (conserver le reste du code existant) ...

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
    
    # Contenu formaté
    pdf.set_font("Arial", size=10)
    
    # Nettoyage du markdown pour le PDF
    lines = contenu.split('\n')
    for line in lines:
        # Gestion des titres
        if line.startswith('### '):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(200, 8, txt=line[4:].strip(), ln=1)
            pdf.set_font('Arial', '', 10)
        # Gestion des listes
        elif line.startswith('- '):
            pdf.cell(10)  # Indentation
            pdf.cell(200, 8, txt='• ' + line[2:].strip(), ln=1)
        else:
            pdf.multi_cell(0, 8, txt=line.strip())
        pdf.ln(2)
    
    # Pied de page
    pdf.set_y(-15)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, f"Généré le {datetime.now(timezone(timedelta(hours=2))).strftime('%d/%m/%Y %H:%M')} par Assistant Prospection Ametis", 0, 0, 'C')
    
    return pdf.output(dest='S').encode('latin1')

# ... (conserver le reste du code existant) ...
