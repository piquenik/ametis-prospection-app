import streamlit as st
import requests
import os
import time

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")
st.title("🥸 Assistant Prospection Ametis")

# Mot de passe obligatoire
password = st.text_input("🔒 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = os.getenv("APP_PASSWORD", "Ametis2025")

if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Saisie utilisateur
nom_entreprise = st.text_input("Nom de l'entreprise")
secteur_cible = st.selectbox("Secteur", ["Agroalimentaire", "Pharma / Cosmétique", "Logistique / Emballage", "Electronique / Technique", "Autre industrie"])

col1, col2 = st.columns([2, 2])
with col1:
    lancer_recherche = st.button("Générer la fiche")
with col2:
    recherche_approfondie = st.button("Recherche approfondie")

if lancer_recherche or recherche_approfondie:
    endpoint = "https://api.deepseek.com/v1/chat/completions"
    model = "deepseek-chat"

    if recherche_approfondie:
        model = "deepseek-reasoner"
        st.markdown("ℹ️ La recherche approfondie peut prendre plus de temps. Source : Deepseek research et source.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"
    }

    # NOUVEAU PROMPT STRUCTURÉ
    prompt = f"""
Tu es un assistant expert en prospection B2B pour Ametis. À partir du nom d'entreprise "{nom_entreprise}" 
et du secteur "{secteur_cible}", génère une fiche de prospection structurée EXACTEMENT comme suit :

### 1. Résumé synthétique
[🏢 Secteur] | [📍 Localisation] 
[1 phrase concise combinant secteur et localisation]

### 2. Description de l'activité
[2-3 phrases descriptives maximum]
- Activité principale : [détail]
- Spécialités : [liste à puces]
- Positionnement marché : [1 phrase]

### 3. Chiffres clés publics
[📊 CA] : [valeur si disponible] | [📈 Tendance]
[👥 Effectifs] : [nombre si disponible] 
[🏭 Sites] : [nombre d'usines/bureaux]
[ℹ️ Source] : [lien vers source publique]

### 4. Signaux d'actualité
[📰 Derniers 6 mois]
- [Signal 1 avec date]
- [Signal 2 avec date]
- [Analyse transformation industrielle en 1 phrase]

### 5. Contacts clés
[🔍 Recherche active - indiquer "Contact non trouvé" si absent]
- **Production** : [Prénom Nom] | [Email/LinkedIn] | [Téléphone]
- **Qualité** : [Prénom Nom] | [Email/LinkedIn] | [Téléphone]
- **Technique** : [Prénom Nom] | [Email/LinkedIn] | [Téléphone]
- **Achats** : [Prénom Nom] | [Email/LinkedIn] | [Téléphone]
- **Marketing** : [Prénom Nom] | [Email/LinkedIn] | [Téléphone]

[Pour toute section sans données, écrire : "Information non disponible - recherche approfondie requise"]

Règles strictes :
1. Ne JAMAIS inventer de contacts - indiquer "Contact non trouvé" si incertain
2. Pour les chiffres : uniquement données vérifiables avec source
3. Maximum 3 signaux d'actualité récents
4. Formatage strict avec les titres de section EXACTS
5. Toujours inclure toutes les sections même si vides
    """

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Tu es un assistant IA expert en prospection B2B. Tu respectes scrupuleusement les formats demandés."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,  # Réduit pour plus de précision
        "max_tokens": 1200   # Augmenté pour la structure détaillée
    }

    with st.spinner(f"🧠 Analyse de {nom_entreprise} en cours..."):
        progress_bar = st.progress(0)
        compteur = st.empty()
        start_time = time.time()

        for i in range(60):
            time.sleep(0.5)
            progress_bar.progress((i + 1) / 60)
            compteur.markdown(f"⏳ Temps écoulé : {i + 1} sec")

        try:
            response = requests.post(endpoint, headers=headers, json=data, timeout=60)
            st.markdown("---")
            
            if response.status_code == 200:
                try:
                    content = response.json()["choices"][0]["message"]["content"]
                    if content.strip():
                        st.success(f"✅ Fiche {nom_entreprise} générée !")
                        st.markdown(content)
                    else:
                        st.warning("⚠️ Réponse vide - vérifiez le nom de l'entreprise")
                except Exception as e:
                    st.error(f"Erreur d'analyse : {str(e)}")
            else:
                st.error(f"❌ Erreur API {response.status_code} : {response.text}")

        except Exception as e:
            st.error(f"❌ Échec de connexion : {str(e)}")
