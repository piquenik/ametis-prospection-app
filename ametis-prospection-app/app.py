import streamlit as st
import openai
import os
from fpdf import FPDF
import tempfile
import smtplib
from email.message import EmailMessage

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
nom_entreprise = st.text_input("Entrez le nom de l'entreprise + departement à analyser")

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

📰 3. Actualités récentes pertinentes :
- Innovations, investissements, recrutement, salon, croissance, certifications...
- Inclure 1 lien source fiable minimum
- Si aucune actualité trouvée, proposer une analyse métier utile (enjeux ou évolution probable)

🔍 4. Analyse contextuelle stratégique :
- Urgence ou criticité du besoin (croissance, traçabilité, automatisation...)
- Profil client : PME, groupe, multisite, bio, artisan...
- Niveau estimé d’investissement ou budget potentiel (si possible)
- Conseil sur le bon timing / angle d’approche (technique, RSE, conformité, ergonomie...)

5. Événements, salons ou réseaux potentiels fréquentés par l’entreprise cible :
Identifie un ou plusieurs événements (salons, foires, webinaires pros, réseaux locaux) où cette entreprise est susceptible d’avoir été présente récemment ou historiquement.
	•	Nom de l’événement (ex : CFIA Rennes, Natexpo, SIRHA…)
	•	Type d’exposition (salon B2B, régional, agro, tech, qualité…)
	•	Si possible : lieu, fréquence (annuel ?), lien ou édition passée
	•	Objectif : pouvoir faire une accroche “nous vous avons vu au…” ou proposer une rencontre lors du prochain

👥 6. Identification des décideurs clés :
- Recherche croisée sur LinkedIn, site, Pappers, presse, annuaires...
- Cibles : production, maintenance, achats, qualité
- Pour chaque : nom, fonction, source estimée, niveau de certitude, fraîcheur de l'info
- Si rien trouvé : générer des profils crédibles selon secteur, taille, structure

🌍 7. Suggestions d’entreprises voisines à prospecter :

À partir de l’adresse de l’entreprise analysée, propose une liste de 3 à 5 entreprises industrielles du même secteur ou d’un secteur complémentaire situées dans un rayon d’environ 50 km (si données disponibles).

- Si les données géographiques ou contextuelles sont insuffisantes, fais une estimation crédible basée sur la zone géographique supposée (ex : région, département, bassin industriel).
- Tu peux utiliser comme base d’inspiration les annuaires d’entreprises (ex : INSEE, Pappers, annuaire-entreprises, salons régionaux ou CFIA).
- Pour chaque entreprise suggérée, indique :
  • Le nom
  • L’activité supposée
  • La commune ou zone estimée
  • L’intérêt potentiel pour Ametis.eu

⚠️ Si aucune information fiable n’est disponible, propose tout de même une **liste fictive réaliste mais clairement signalée comme générée à partir de corrélations régionales** (ex : “suggestions basées sur des entreprises agroalimentaires typiques dans le secteur de Laval (53)”).

✉️ 8. Email de prospection combiné Production + Qualité :
- Objet personnalisé lié à un enjeu identifié
- Introduction contextualisée
- Bloc combiné Production + Qualité (automatisation, conformité, réduction des erreurs, traçabilité)
- Ajouter un cas client ou bénéfice mesurable si pertinent
- Appel à action clair : visio ou appel proposé

⚠️ Si les données sont absentes ou incomplètes, tu dois SIMULER une fiche complète crédible basée sur le secteur, le type d’entreprise, et la région. Ne JAMAIS rendre une fiche vide.

🌍 9. Suggestions d’entreprises voisines à prospecter :

À partir de l’adresse de l’entreprise analysée, propose une liste de 5 à 10 entreprises industrielles du même secteur dans les 50 Kilometres  ou d’un secteur complémentaire situées dans un rayon d’environ 50 km.

- Si l’adresse n’est pas trouvée, effectue une estimation crédible (région, département, bassin industriel).
- Utilise comme inspiration les annuaires publics (INSEE, Pappers, CFIA, etc.).
- Pour chaque entreprise suggérée, indique :
  • Le nom  
  • L’activité estimée  
  • La commune  
  • L’intérêt potentiel pour Ametis.eu

  Genere une carte Maps incluant les entreprises proposées sur la carte .

  🔢 10. Chiffre d’affaires estimé (année N-1 ou dernière connue) :
- Recherche et indique le chiffre d'affaires annuel le plus récent disponible pour l’entreprise (idéalement N-1).
- Si la donnée est publique, mentionne :
  - Le montant, la source (ex. : Pappers, société.com, rapport annuel, article)
  - Et l’année de référence (ex. : exercice 2022, publication 2024).
- ⚠️ Si aucune donnée fiable n’est trouvée :
  - Mentionne clairement : “Chiffre d'affaires non disponible publiquement”
  - Et propose une estimation crédible basée sur :
    - l’effectif,
    - le secteur d’activité,
    - le positionnement marché (GMS, B2B, RHF…),
    - des entreprises similaires connues.

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
from fpdf import FPDF

if st.session_state.fiche_prospection:
    st.markdown("📄 **Exporter la fiche au format PDF**")
    
    if st.button("📥 Télécharger le PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)

        for line in st.session_state.fiche_prospection.split('\n'):
            pdf.multi_cell(0, 10, line)

        pdf_path = "/tmp/fiche_prospection.pdf"
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            st.download_button("📄 Télécharger le fichier PDF", f, file_name="fiche_prospection.pdf")
        except Exception as e:
            st.error(f"Une erreur est survenue : {e}")
else:
    st.info("Entrez un nom d'entreprise pour générer une fiche.")
