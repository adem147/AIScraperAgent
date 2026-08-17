"""Various Examples Demo: Random JSON, Good JSON, and Random Raw Text.
Run with: python various_examples_demo.py
"""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from LLM import get_pipeline

# ==============================================================================
# EXAMPLE 1: RANDOM / MESSY JSON (Weird key names from an arbitrary scraper)
# ==============================================================================
RANDOM_MESSY_JSON = {
    "tender_heading": "Modernization of National Cyber Defense & SOC Infrastructure",
    "agency_owner": "Ministry of Communication Technologies (MTC) / CERT",
    "deadline_iso": "2026-10-15T15:00:00Z",
    "est_val": "750,000 TND",
    "country_code": "TN",
    "allocations": [
        {"code": "L1", "label": "SIEM Software & EDR Endpoint Agents", "cost": "400k TND"},
        {"code": "L2", "label": "SOC Integration & 24/7 Threat Hunting Services", "cost": "350k TND"}
    ],
    "mandatory_papers": [
        "Bid Bond Guarantee (7,500 TND)",
        "ISO 27001 Company Certification",
        "Fiscal clearance certificate (Quitus fiscal)"
    ],
    "eligibility_rules": [
        "At least 5 years operating an accredited SOC",
        "Minimum 3 verified references in telecom or banking sector"
    ]
}

# ==============================================================================
# EXAMPLE 2: GOOD / CONVENTIONAL JSON (Well-structured API response)
# ==============================================================================
GOOD_STRUCTURED_JSON = {
    "id": "WB-PROC-2026-991",
    "title": "Cloud Computing Infrastructure & Microservices Architecture Consultancy",
    "organization": "African Development Bank (AfDB)",
    "country": "Regional / Tunisia",
    "sector": "Information & Communications Technologies",
    "submission_deadline": "2026-09-20",
    "budget": {
        "amount": 220000.0,
        "currency": "EUR",
        "formatted": "220,000 EUR"
    },
    "description": "Consultancy firm to design, build, and deploy Kubernetes clusters, secure API gateways, and CI/CD automated deployment pipelines for government digital portals.",
    "criteres": [
        "CKA (Certified Kubernetes Administrator) certified lead engineer",
        "Proven experience deploying microservices on AWS or Azure"
    ],
    "documents_requis": [
        "Technical methodology",
        "Financial cost breakdown",
        "3 client reference letters"
    ]
}

# ==============================================================================
# EXAMPLE 3: RANDOM UNSTRUCTURED TEXT (Mixed Arabic/French Tender Notice)
# ==============================================================================
RANDOM_UNSTRUCTURED_TEXT = """
الجمهورية التونسية - وزارة تكنولوجيات الاتصال
AVIS D'APPEL À MANIFESTATION D'INTÉRÊT (AMI) N° 09/2026
الموضوع: Sélection d'un cabinet d'ingénierie pour le développement de modèles d'Intelligence Artificielle et de Traitement Automatique du Langage Naturel (NLP) pour les services administratifs.
المشتري العمومي: Centre d'Études et de Recherche des Télécommunications (CERT).
Budget prévisionnel: 180 000 DT TTC.
Délai de soumission: 05 Octobre 2026 à 11h00 au bureau d'ordre central.
Critères de qualification:
- Cabinet disposant d'une équipe spécialisée en Data Science et NLP (Python, HuggingFace, LLMs).
- Réalisation d'au moins 2 projets similaires d'IA dans le secteur public ou télécom.
Documents à fournir:
- Cautionnement provisoire de 1 800 TND.
- Offre technique détaillée avec CVs des experts.
- Attestation fiscale et attestation CNSS valides.
"""


def print_comparison(title, input_data, notice):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

    print("\n[1] INPUT GIVEN TO THE SYSTEM:")
    print("-" * 80)
    if isinstance(input_data, dict):
        print(json.dumps(input_data, indent=2, ensure_ascii=False))
    else:
        print(input_data.strip())
    print("-" * 80)

    print("\n[2] OUTPUT: STANDARDIZED UNIVERSAL JSON SCHEMA:")
    print("-" * 80)
    output_dict = notice.model_dump()
    # Pretty print output JSON
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))
    print("-" * 80)

    score_pct = round(notice.relevance_score * 100, 1)
    badge = "✅ PERTINENT (≥ 70%)" if notice.is_relevant else "❌ NON PERTINENT (< 70%)"
    rec = notice.analyse_faisabilite.recommandation if notice.analyse_faisabilite else "N/A"
    
    print("\n[3] DECISION SUMMARY:")
    print(f" • Objet / Subject   : {notice.objet}")
    print(f" • Buyer / Organisme : {notice.organisme}")
    print(f" • Budget            : {notice.budget.formatted if notice.budget else 'N/A'}")
    print(f" • Deadline          : {notice.dates.submission_deadline}")
    print(f" • Relevance Score   : {score_pct}%  -->  {badge}")
    print(f" • Decision          : {rec}")
    print("=" * 80)


def main():
    pipeline = get_pipeline()

    print("\n" + "#" * 80)
    print("  AIScraperAgent — DEMONSTRATION OF VARIOUS INPUT TYPES")
    print("#" * 80)
    print(" [1] Test Random / Messy JSON (Weird key names)")
    print(" [2] Test Good / Structured JSON (Standard API format)")
    print(" [3] Test Random Unstructured Raw Text (Arabic / French mixed)")
    print(" [4] Run All 3 Examples Sequentially")
    print("-" * 80)

    choice = input("Select an option [1-4]: ").strip()

    if choice == "1" or choice == "4":
        print("\nProcessing Example 1: Random / Messy JSON...")
        n1 = pipeline.process(RANDOM_MESSY_JSON, persist_db=False)
        print_comparison("EXAMPLE 1: RANDOM / MESSY JSON", RANDOM_MESSY_JSON, n1)

    if choice == "2" or choice == "4":
        print("\nProcessing Example 2: Good / Conventional JSON...")
        n2 = pipeline.process(GOOD_STRUCTURED_JSON, persist_db=False)
        print_comparison("EXAMPLE 2: GOOD / STRUCTURED JSON", GOOD_STRUCTURED_JSON, n2)

    if choice == "3" or choice == "4":
        print("\nProcessing Example 3: Random Unstructured Raw Text...")
        n3 = pipeline.process(RANDOM_UNSTRUCTURED_TEXT, persist_db=False)
        print_comparison("EXAMPLE 3: RANDOM UNSTRUCTURED RAW TEXT", RANDOM_UNSTRUCTURED_TEXT, n3)


if __name__ == "__main__":
    main()
