from nvidia_client import generate_json

SYSTEM_PROMPT = """
You are an information extraction system.

Extract structured public procurement data from text.

Rules:
- Output ONLY valid JSON
- Do not add explanations
- If a field is missing, return null
- Use ISO format for dates (YYYY-MM-DD)

Schema:
{
    title : String
  
    description : String
  
    document_url : String   
  
    submission_deadline : DateTime
  
    sector : String
}
"""


def extract_from_text(text, source_name=None, source_url=None, notice_id=None):
    """Extract structured procurement entities from raw text."""
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty.")

    prompt = f"""
    TEXT:
    {text.strip()}
    """
    
    return generate_json(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=2048,
    )


test_text = """
REPUBLIQUE TUNISIENNE

Instance Nationale des Télécommunications

M.fiscal : 831285C/A/M

AVIS d’appel d’offres N° 07/2025

Acquisition d’équipements informatiques

 

L’Instance Nationale des Télécommunications se propose de lancer un appel d’offres pour l’acquisition d’équipements informatiques, se composant de trois lots :  

-lot 1 : Serveur central SIG ;

-lot 2:  Laptop professionnel ;

-Lot 3 : Extension Data Center ;

L’appel d’offres est ouvert à tout établissement justifiant qu’il possède toutes les compétences et les garanties requises pour assurer la bonne exécution du présent appel d’offres.

Les personnes physiques ou morales désirant participer peuvent demander gratuitement une version électronique du cahier des charges s’y rapportant à compter du 26 novembre 2025, en remplissant le formulaire disponible sur ce lien et en l’envoyant à l’adresse suivante spm@intt.tn

Les offres devront parvenir à l’INT, sous pli postal fermé et recommandé ou par l'intermédiaire d’un service postale rapide ou être remises directement au bureau d’ordre de l’INT contre remise d’un récépissé et ce au plus tard le 26 décembre 2025 à 10h00 (heure locale). Le cachet du bureau d’ordre de l’INT fait foi.

L’offre financière et les documents administratifs seront placés dans deux enveloppes séparées, fermées et scellées. Ces deux enveloppes et le cautionnement provisoire seront placés dans une troisième enveloppe fermée et scellée indiquant la référence de l’appel d’offres et son objet et portant la mention :

 À ne pas ouvrir

AVIS d’appel d’offres N° 07/2025

 

« Acquisition d’équipements informatiques »

    

L’ouverture des plis est publique et aura lieu à la salle de réunion (4ème étage) au siège de l’INT et ce le 26 décembre 2025 à 10h30 (heure locale)."""
print(extract_from_text(test_text))