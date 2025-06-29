import streamlit as st
import openai
import os

# Configuration API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configuration de la page
st.set_page_config(page_title="Assistant Prospection Ametis", layout="centered")

st.title("🧐 V1.0 Prospection Ametis.eu")
st.markdown("""
Cet assistant vous permet d'obtenir une fiche complète de prospection enrichie à partir du nom d'une entreprise. Il est conseille d'indiquer le nom suivi du numero de son departement ( ex : Actibio 53 )

Chaque fiche inclut :
- Les coordonnées complètes et visuelles (logo + site web)
- Une présentation synthétique de l’activité
- Les actualités ou signaux faibles de transformation
- Les contacts clés (production, technique, achats, qualité)
- Un email de prospection combiné (production + qualité)
- Des données contextuelles : criticité du besoin, profil client, budget estimé, stratégie d’approche
- Une carte et suggestions d'entreprises voisines dans un rayon de 50 km
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
Tu es un assistant IA expert en prospection commerciale B2B pour le compte d’Ametis.eu, spécialiste de :
- la traçabilité industrielle,
- les étiqueteuses et imprimantes industrielles,
- les consommables (étiquettes, rubans transfert thermique),
- l’intégration ERP/WMS et solutions logicielles,
- le mobilier logistique mobile,
- les environnements agroalimentaires exigeants (humidité, lavage, IFS/BRC).

Ton utilisateur est responsable commercial secteur agroalimentaire. L’entreprise cible est : {nom_entreprise}.

Ta mission est de générer une fiche de prospection complète, claire et directement exploitable. Tu dois absolument générer toutes les sections jusqu'à l'étape 8, même en cas d'absence de données concrètes (dans ce cas, fournis des estimations ou des exemples fictifs crédibles).

---

📇 1. Informations de contact :
- Adresse postale complète
- Téléphone général
- Email public (si disponible)
- Effectif estimé
- Site internet (si trouvé)
- Logo (lien image ou site)

🏭 2. Présentation synthétique (5 lignes max) :
- Type : fabricant, transformateur, distributeur ?
- Produits ou services
- Marchés visés (GMS, export, RHF...)
- Certifications ou labels (Bio, IFS, BRC...)
- Contraintes industrielles connues (traçabilité, automatisation, hygiène...)
-Chiffre d'affaire de l'année N-1

📰 3. Actualités récentes pertinentes :
- Innovations, investissements, recrutement, salon, croissance, certifications...
- Inclure 1 lien source fiable minimum
- Si aucune actualité trouvée, proposer une analyse métier utile (enjeux ou évolution probable)

🔍 4. Analyse contextuelle stratégique :
- Urgence ou criticité du besoin (croissance, traçabilité, automatisation...)
- Profil client : PME, groupe, multisite, bio, artisan...
- Niveau estimé d’investissement ou budget potentiel (si possible)
- Conseil sur le bon timing / angle d’approche (technique, RSE, conformité, ergonomie...)

👥 5. Identification des décideurs clés :
- Recherche croisée sur LinkedIn, site, Pappers, presse, annuaires...
- Cibles : production, maintenance, achats, qualité
- Pour chaque : nom, fonction, source estimée, niveau de certitude, fraîcheur de l'info
- Si rien trouvé : générer des profils crédibles selon secteur, taille, structure

🌍 6. Suggestions d’entreprises voisines à prospecter :

À partir de l’adresse de l’entreprise analysée, propose une liste de 3 à 5 entreprises industrielles du même secteur ou d’un secteur complémentaire situées dans un rayon d’environ 50 km (si données disponibles).

- Si les données géographiques ou contextuelles sont insuffisantes, fais une estimation crédible basée sur la zone géographique supposée (ex : région, département, bassin industriel).
- Tu peux utiliser comme base d’inspiration les annuaires d’entreprises (ex : INSEE, Pappers, annuaire-entreprises, salons régionaux ou CFIA).
- Pour chaque entreprise suggérée, indique :
  • Le nom
  • L’activité supposée
  • La commune ou zone estimée
  • L’intérêt potentiel pour Ametis.eu

⚠️ Si aucune information fiable n’est disponible, propose tout de même une **liste fictive réaliste mais clairement signalée comme générée à partir de corrélations régionales** (ex : “suggestions basées sur des entreprises agroalimentaires typiques dans le secteur de Laval (53)”).

✉️ 7. Email de prospection combiné Production + Qualité :
- Objet personnalisé lié à un enjeu identifié
- Introduction contextualisée
- Bloc combiné Production + Qualité (automatisation, conformité, réduction des erreurs, traçabilité)
- Ajouter un cas client ou bénéfice mesurable si pertinent
- Appel à action clair : visio ou appel proposé

⚠️ Si les données sont absentes ou incomplètes, tu dois SIMULER une fiche complète crédible basée sur le secteur, le type d’entreprise, et la région. Ne JAMAIS rendre une fiche vide.

🌍 8. Suggestions d’entreprises voisines à prospecter :

À partir de l’adresse de l’entreprise analysée, propose une liste de 5 à 10 entreprises industrielles du même secteur dans les 50 Kilometres  ou d’un secteur complémentaire situées dans un rayon d’environ 50 km.

- Si l’adresse n’est pas trouvée, effectue une estimation crédible (région, département, bassin industriel).
- Utilise comme inspiration les annuaires publics (INSEE, Pappers, CFIA, etc.).
- Pour chaque entreprise suggérée, indique :
  • Le nom  
  • L’activité estimée  
  • La commune  
  • L’intérêt potentiel pour Ametis.eu

  Genere une carte Maps incluant les entreprises proposées

⚠️ Si aucune donnée n’est disponible, crée une **liste fictive crédible**, clairement signalée comme simulée.
Tu dois absolument générer l’étape 8, même si les données sont estimées ou fictives”.

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
                max_tokens=3000
            )
            fiche = response["choices"][0]["message"]["content"]
            st.markdown("---")
            st.markdown(f"**Fiche pour : {nom_entreprise}**")
            st.markdown(fiche)

            if "✉️ 7." in fiche:
                start = fiche.find("✉️ 7.")
                email_section = fiche[start:]
                st.download_button("📋 Copier l’e-mail (en texte)", email_section, file_name="email_prospection.txt")

        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
else:
    st.info("Entrez un nom d'entreprise pour générer une fiche.")
