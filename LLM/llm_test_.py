from llm_client import ask_llm,ask_ollama

SYSTEM_PROMPT = """
You are an information extraction system.

Extract structured public procurement data from text.

Rules:
- Output ONLY valid JSON
- Do not add explanations
- If a field is missing, return null
- Use ISO format for dates (YYYY-MM-DD)

TARGET SCHEMA:
{
  "title": null,
  "description": null,
  "url": null,
  "published_date": null,
  "submission_deadline": null,
  "sector": null,
  "country": null
}

MAPPING GUIDELINES:
- "title": field representing the main object (what is being procured)
- "description": field containing descriptive or detailed text
- "submission_deadline": field containing a closing or deadline date
- "published_date": field representing publication date, release date, or announcement date
- "url": field containing a URL or link
- "sector": field representing category, domain, or industry
- "country": field representing the country where the project or procurement is located or assigned
"""
TEXT = """REPUBLIQUE TUNISIENNE 

Instance Nationale des Télécommunications

M.fiscal : 831285C/A/M

AVIS d’APPEL D’OFFRES N° 06/2025

Acquisition d’une plateforme de mesure pour l’évaluation de la QOS Internet fixe

 

L’Instance Nationale des Télécommunications se propose de lancer un Appel d’Offres pour l’acquisition d’une plateforme de mesure pour l’évaluation de la QOS Internet Fixe

Peuvent participer au présent appel d'offres toute personne physique ou morale tunisienne ou étrangère, ou groupement, justifiant qu’il possède toutes les compétences et les garanties requises pour assurer, dans de bonnes conditions, l’exécution de ce marché.

Les personnes désirant participer peuvent demander gratuitement une version électronique du cahier des charges s’y rapportant à compter du 06 novembre 2025 en remplissant le formulaire disponible sur ce lien et en l’envoyant à l’adresse suivante spm@intt.tn .

Les offres devront parvenir à l’INT, sous pli postal fermé et recommandé ou par l'intermédiaire d’un service postale rapide ou être remises directement au bureau d’ordre de l’INT contre remise d’un récépissé et ce au plus tard le 08 décembre 2025 à 10h00 (heure locale). Le cachet du bureau d’ordre de l’INT fait foi.

L’offre technique et l’offre financière seront placées dans deux enveloppes séparées, fermées et scellées. Ces deux enveloppes, les documents administratifs seront placés dans une troisième enveloppe fermée et scellée indiquant la référence de l’appel d’offres et son objet et portant la mention :

 À ne pas ouvrir

Appel d’Offres N° 06/2025

 

« Acquisition d’une plateforme de mesure pour l’évaluation de la QOS Internet fixe »

    

L’ouverture des plis est publique et aura lieu à la salle de réunion (4ème étage) au siège de l’INT et ce le 08 décembre 2025 à 10h30 (heure locale) -Rue Echabia Montplaisir 1073 Tunis. """

result = ask_llm(
    "Explain what an API endpoint is in one sentence."
)

print(ask_ollama(SYSTEM_PROMPT,TEXT))
