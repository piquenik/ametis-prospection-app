import streamlit as st
import openai
import os

# Configuration API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")


st.title("🧐 Assistant Prospection Ametis.eu")
st.markdown("""
Cet assistant vous permet d'obtenir une fiche complète de prospection enrichie à partir du nom d'une entreprise. 

Chaque fiche inclut :
- Les coordonnées complètes et visuelles (logo + site web)
- Une présentation synthétique de l’activité
- Les actualités ou signaux faibles de transformation
- Les contacts clés (production, technique, achats, qualité)
- Un email de prospection combiné (production + qualité)
- Des données contextuelles : criticité du besoin, profil client, budget estimé, stratégie d’approche
""")

# Mot de passe obligatoire
password = st.text_input("🔒 Veuillez entrer le mot de passe pour accéder à l'outil :", type="password")
CORRECT_PASSWORD = os.getenv("AMETIS_PASS", "Ametis2025")

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

    Voici le nom de l’entreprise à traiter : {nom_entreprise}

    Tu dois fournir une fiche de prospection enrichie structurée comme suit :

    📇 1. Coordonnées complètes :
    - Adresse postale
    - Téléphone général
    - Email public (si disponible)
    - Effectif estimé
    - Site Internet (si disponible)
    - Logo de l’entreprise (lien direct vers l’image si trouvable)

    🏭 2. Présentation synthétique (5 lignes max) :
    - Fabricant / distributeur / transformateur ?
    - Produits ou services proposés
    - Marchés visés
    - Certifications ou labels
    - Contraintes industrielles identifiées (traçabilité, nettoyage, automatisation…)

    📰 3. Actualités pertinentes :
    - Innovations, investissements, développement durable, salons, recrutements, certifications
    - Inclure au moins 1 lien source fiable
    - Si aucune actualité, fournir une analyse métier utile à la prospection

    🔍 4. Analyse contextuelle stratégique :
    - Criticité ou urgence potentielle du besoin (croissance, automatisation, IFS...)
    - Typologie de client : groupe, PME, artisan, exportateur, bio, multisite ?
    - Estimation du budget ou niveau d’investissement (selon taille, CA, automatisation)
    - Recommandation stratégique : canal de contact, timing idéal, angle d’approche (technique, RSE, logistique, qualité...)

    👥 5. Identification des décideurs clés :
    Recherche croisée sur : LinkedIn, site entreprise, presse, Pappers, annuaires salons
    - Responsable production / Directeur industriel
    - Responsable technique / Maintenance
    - Responsable achats / Approvisionnement
    - Responsable qualité / QHSE
    Pour chaque contact : nom, fonction, source estimée, fraîcheur de l'info, niveau de certitude

    ✉️ 6. Email de prospection personnalisé combiné (Production + Qualité) :
    - Objet accrocheur (lié à une actualité ou un enjeu métier identifié)
    - Introduction personnalisée
    - Bloc combiné Production + Qualité (automatisation, traçabilité, conformité, réduction des erreurs)
    - Ajoute si possible un exemple client ou bénéfice constaté
    - Call-to-action clair (proposition de visio ou appel rapide)
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

            if "✉️ 6." in fiche:
                start = fiche.find("✉️ 6.")
                email_section = fiche[start:]
                st.download_button("📋 Copier l’e-mail (en texte)", email_section, file_name="email_prospection.txt")

        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
else:
    st.info("Entrez un nom d'entreprise pour générer une fiche.")
