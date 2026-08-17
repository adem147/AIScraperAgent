import json
from typing import Dict, Any, Optional
from .nvidia_client import NvidiaLLMClient, get_nvidia_client
from .schemas import ProcurementNotice, FeasibilityAnalysis


FEASIBILITY_ANALYSIS_SYSTEM_PROMPT = """You are a Senior Strategic Bid Manager & Technical Director at CERT (Centre d'Études et de Recherche des Télécommunications).
Your task is to analyze a public procurement opportunity (AMI / Appel d'Offres) and generate:
1. An Executive Synthesis of the Opportunity ('synthese_opportunite') in clear, professional French.
2. A Preliminary Feasibility Analysis ('analyse_faisabilite') evaluating technical capability match, required profiles, potential operational/legal risks, and a GO / NO-GO recommendation.

CERT Core Capabilities:
- Telecommunications & 5G/4G, Radio Frequency, IoT
- Artificial Intelligence, Machine Learning, Data Analytics, NLP/LLMs
- Cybersecurity, SOC/SIEM, Security Audits, ISO 27001
- Cloud Architecture, DevOps, Enterprise Web Platforms, Digital Transformation

Target Output JSON Schema:
{
  "synthese_opportunite": "Detailed 2-3 paragraph executive summary covering context, objectives, deliverables, timeline, and key requirements...",
  "analyse_faisabilite": {
    "adequation_technique": "Detailed analysis of technical alignment with CERT capabilities...",
    "competences_requises": [
      "Key technical skill / role 1 (e.g. Lead DevOps & Cloud Architect)",
      "Key technical skill / role 2 (e.g. Senior AI/NLP Engineer)",
      "Key technical skill / role 3 (e.g. Certified Cybersecurity Specialist)"
    ],
    "risques_et_contraintes": [
      "Identified risk 1 (e.g. Délai de soumission serré)",
      "Identified risk 2 (e.g. Cautionnement bancaire / garantie financière requise)",
      "Identified risk 3 (e.g. Références requises sur projets similaires de plus de 3 ans)"
    ],
    "recommandation": "GO | NO-GO | A_ETUDIER_AVEC_PARTENAIRE",
    "score_faisabilite": 0.85
  }
}

Guidelines:
- Output strictly valid JSON without conversational text or markdown code fences.
- Recommandation values MUST be one of: 'GO', 'NO-GO', 'A_ETUDIER_AVEC_PARTENAIRE'.
- Ensure the synthesis is insightful, concise, and structured for decision-makers.
"""


class FeasibilityAnalyser:
    """Generates executive opportunity syntheses and preliminary feasibility analyses."""

    def __init__(self, client: Optional[NvidiaLLMClient] = None):
        self.client = client or get_nvidia_client()

    def analyze_opportunity(self, notice: ProcurementNotice) -> ProcurementNotice:
        """Enrich a ProcurementNotice with executive summary and feasibility analysis."""
        prompt = (
            f"Please conduct the opportunity synthesis and preliminary feasibility analysis for the following notice:\n\n"
            f"Titre/Objet: {notice.objet}\n"
            f"Organisme: {notice.organisme}\n"
            f"Secteur: {notice.sector or 'Non précisé'}\n"
            f"Pays: {notice.country or 'Non précisé'}\n"
            f"Langue d'origine: {notice.language}\n"
            f"Date limite de soumission: {notice.dates.submission_deadline or 'Non précisée'}\n"
            f"Budget: {notice.budget.formatted if notice.budget else 'Non précisé'}\n"
            f"Critères d'éligibilité: {', '.join(notice.criteres) if notice.criteres else 'Standards'}\n"
            f"Lots: {', '.join([l.title for l in notice.lots]) if notice.lots else 'Lot Unique'}\n"
            f"Documents requis: {', '.join(notice.documents_requis) if notice.documents_requis else 'Documents usuels'}\n"
            f"Score de pertinence estimé: {notice.relevance_score} (Pertinent: {notice.is_relevant})\n"
        )

        try:
            result = self.client.generate_json(
                prompt=prompt,
                system_prompt=FEASIBILITY_ANALYSIS_SYSTEM_PROMPT,
                max_tokens=2048,
            )

            synthese = result.get("synthese_opportunite")
            feas_raw = result.get("analyse_faisabilite") or {}

            if feas_raw:
                feasibility = FeasibilityAnalysis(
                    adequation_technique=feas_raw.get(
                        "adequation_technique", "Alignement technique évalué."
                    ),
                    competences_requises=feas_raw.get("competences_requises", []),
                    risques_et_contraintes=feas_raw.get("risques_et_contraintes", []),
                    recommandation=feas_raw.get("recommandation", "GO" if notice.is_relevant else "NO-GO"),
                    score_faisabilite=float(feas_raw.get("score_faisabilite", notice.relevance_score)),
                )
                notice.analyse_faisabilite = feasibility

            notice.synthese_opportunite = synthese or f"Opportunité relative à {notice.objet} émise par {notice.organisme}."

        except Exception as e:
            print("Feasibility analysis exception:", e)
            notice.synthese_opportunite = f"Synthèse: Appel d'offres concernant '{notice.objet}' publié par {notice.organisme}."
            notice.analyse_faisabilite = FeasibilityAnalysis(
                adequation_technique="Évaluation par défaut.",
                competences_requises=["Ingénierie Logicielle / Télécom"],
                risques_et_contraintes=["Délai de soumission"],
                recommandation="GO" if notice.is_relevant else "NO-GO",
                score_faisabilite=notice.relevance_score,
            )

        return notice
