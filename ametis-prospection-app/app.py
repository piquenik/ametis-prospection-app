import streamlit as st
import requests
import time
from fpdf import FPDF
import tempfile
import socket

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

# Fonction pour vérifier la connectivité Internet
def check_internet_connection():
    try:
        # Test de connexion à un serveur DNS fiable
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

# Solution de repli locale améliorée
def generate_fallback_report(company, sector):
    return f"""
# 🧐 Fiche Prospection: {company}

**Secteur:** {sector}  
**Date de génération:** {time.strftime("%d/%m/%Y")}

## 📌 Coordonnées
- **Adresse:** Non disponible (erreur API)
- **Site web:** www.{company.replace(' ', '').lower()}.fr
- **Téléphone:** 01 23 45 67 89

## 🏢 Activité principale
Entreprise spécialisée dans le secteur {sector.lower()}. Description générée localement - L'API DeepSeek n'a pas répondu.

## 👥 Contacts clés
- **Responsable production:** contact@{company.replace(' ', '').lower()}.fr
- **Responsable qualité:** qualite@{company.replace(' ', '').lower()}.fr

## ✉️ Stratégie d'approche
Privilégier un contact par email avec proposition de démonstration gratuite des solutions Ametis:

> Objet: Solution de traçabilité pour votre production  
>  
> Bonjour,  
>  
> Nous proposons des solutions innovantes de traçabilité spécialement adaptées au secteur {sector.lower()}.  
> Pouvons-nous planifier un court échange la semaine prochaine?  
>  
> Cordialement,  
> [Votre nom]  
> Ametis.eu

## 📊 Données contextuelles
- **Criticité du besoin:** Élevée
- **Budget estimé:** 15 000 - 20 000 €
- **Période d'achat:** Prochain trimestre
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
    company = st.text_input("Nom de l'entreprise", "ACTIBIO 53")
    sector = st.selectbox("Secteur", ["Agroalimentaire", "Pharma/Cosmétique", "Logistique", "Industrie", "Autre"], index=0)
    
    if st.button("Générer la fiche", type="primary"):
        if not company:
            st.warning("Veuillez saisir un nom d'entreprise")
            return
            
        # Vérification de la connexion Internet
        if not check_internet_connection():
            st.error("Pas de connexion Internet détectée. Veuillez vérifier votre réseau.")
            fiche = generate_fallback_report(company, sector)
            st.session_state.fiche = fiche
            st.markdown(fiche)
            return
            
        # Mode démo - Utilisation directe du fallback
        st.warning("Mode démo activé - Utilisation du modèle local")
        fiche = generate_fallback_report(company, sector)
        st.session_state.fiche = fiche
        st.markdown(fiche)

    # Export PDF
    if st.session_state.get('fiche'):
        if st.button("📄 Exporter en PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Ajout du logo en haut à gauche
            try:
                pdf.image("logo-ametis.png", x=10, y=8, w=30)
            except:
                pass
                
            pdf.ln(20)  # Espace après le logo
            
            for line in st.session_state.fiche.split('\n'):
                # Ignorer les lignes vides
                if not line.strip():
                    pdf.ln(8)
                    continue
                    
                # Style pour les titres
                if line.startswith("# "):
                    pdf.set_font("Arial", "B", 16)
                    pdf.cell(0, 10, line[2:], ln=True)
                    pdf.set_font("Arial", size=12)
                elif line.startswith("## "):
                    pdf.set_font("Arial", "B", 14)
                    pdf.cell(0, 10, line[3:], ln=True)
                    pdf.set_font("Arial", size=12)
                else:
                    pdf.cell(0, 8, line, ln=True)
            
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
