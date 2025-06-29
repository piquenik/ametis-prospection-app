import streamlit as st
import openai
import os

# Configuration API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")


st.title(" Prospection – Ametis.eu")
st.markdown("""
Cet assistant vous permet d'obtenir une fiche complète de prospection à partir du nom d'une entreprise.
""")

# Mot de passe obligatoire
password = st.text_input("🔒 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = os.getenv("AMETIS_PASS", "Ametis2025")  # peut être défini comme secret Streamlit

if password != CORRECT_PASSWORD:
    st.warning("Accès restreint – veuillez entrer le mot de passe.")
    st.stop()

# Champ de saisie de l'entreprise
nom_entreprise = st.text_input("Entrez le nom de l'entreprise à analyser")

if st.button("Générer la fiche") and nom_entreprise:
    prompt = f"""
    Tu es un assistant IA expert en prospection commerciale B2B, dédié à l’entreprise Ametis.eu, spécialisée dans :
    • la traçabilité industrielle,
    • les étiqueteuses et imprimantes industrielles,
    • les consommables (étiquettes, rubans transfert thermique),
    • l’intégration ERP/WMS et solutions logicielles sur-mesure,
    • le mobilier logistique mobile (postes de travail, imprimantes embarquées…),
    • les environnements agroalimentaires exigeants (humidité, nettoyage, normes IFS/BRC…).

    Ton utilisateur est responsable commercial secteur agroalimentaire.

    Voici le nom de l’entreprise à traiter : {nom_entreprise}

    Tu dois fournir :

    📇 1. Coordonnées complètes :
    - Adresse postale
    - Téléphone général
    - Email public (si disponible)
    - Effectif estimé

    🏭 2. Présentation synthétique (5 lignes max) :
    - Fabricant / distributeur / transformateur ?
    - Produits ou services proposés
    - Marchés visés
    - Certifications ou labels
    - Contraintes industrielles identifiées (traçabilité, nettoyage, automatisation…)

    📰 3. Actualités pertinentes (récentes et exploitables pour la prospection) :
    - Innovations, investissements, développement durable, salons, recrutements, certifications
    - Inclure au moins 1 lien source
    - ⚠️ Si aucune actualité pertinente, faire une analyse métier crédible pour identifier un enjeu prospectif lié aux solutions Ametis.eu

    👥 5. Identification des décideurs clés :

Fais une recherche croisée sur toutes les données publiques disponibles sur Internet (LinkedIn, presse, site corporate, communiqués, annuaires) afin d'identifier les noms et fonctions suivants, s’ils sont trouvables publiquement :

• Responsable de production / Directeur industriel  
• Responsable technique / Directeur technique / Maintenance  
• Responsable des achats  
• Directeur des opérations / Directeur de site

Pour chaque personne trouvée :
- indique le nom, le poste exact, et l'entreprise associée  
- précise la source estimée (ex : LinkedIn, site société, presse)  
- donne une indication de fraîcheur (ex : “Profil actif en mai 2024”, “publication récente”, etc.)  
- si le nom n’est pas trouvable, indique-le clairement avec “non trouvé publiquement”

✉️ 4. Email de prospection personnalisé combiné (Production + Qualité) :
    - 🎯 Objet accrocheur (lié à une actualité ou un enjeu métier identifié)
    - 📌 Introduction personnalisée
    - ⚙️ Bloc combiné Production + Qualité (automatisation, traçabilité, conformité, réduction des erreurs)
    - 🧩 Ajouter exemple client ou impact métier si possible
    - 📅 Proposition de visio ou appel de 15 min
    """

    with st.spinner("Recherche en cours et génération de la fiche..."):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un assistant IA spécialisé en prospection B2B pour l'industrie agroalimentaire."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1800
            )
            fiche = response["choices"][0]["message"]["content"]
            st.markdown("---")
            st.markdown(f"**Fiche pour : {nom_entreprise}**")
            st.markdown(fiche)

            if "✉️ Email de prospection" in fiche:
                start = fiche.find("✉️ Email de prospection")
                email_section = fiche[start:]
                st.download_button("📋 Copier l’e-mail (en texte)", email_section, file_name="email_prospection.txt")

        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
else:
    st.info("Entrez un nom d'entreprise pour générer une fiche.")
