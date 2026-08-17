"""Demo: Showing raw unstructured text being converted into a Universal JSON Schema.
Run with: python show_transformer_demo.py
"""

import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from LLM import get_pipeline

# 1. RAW UNSTRUCTURED TEXT (Messy copied text from an announcement)
RAW_UNSTRUCTURED_TEXT = """
*** APPEL D'OFFRES INTERNATIONAL ***
Réf: AOI-2026-CERT-AI
Le Centre d'Études et de Recherche des Télécommunications (CERT) basé à Tunis lance une consultation 
pour la mise en place d'une infrastructure d'Intelligence Artificielle générative et de traitement NLP multilingue 
pour l'automatisation des services publics.
Montant alloué: environ 500 000 Dinars Tunisiens (500 000 TND).
La date limite pour déposer les offres au bureau d'ordre est fixée impérativement au 28 Septembre 2026 à 12h00.
L'ouverture publique des enveloppes aura lieu le 28 Septembre 2026 à 14h30.
Le projet comprend deux lots distincts:
Lot n°1: Fourniture des serveurs de calcul GPU et stockage haute performance (Budget estimatif: 300 000 TND).
Lot n°2: Développement des modèles d'IA, pipelines de données et API REST (Budget estimatif: 200 000 TND).
Conditions de participation:
- Les soumissionnaires doivent avoir au moins 4 ans d'expérience dans le déploiement de clusters GPU et modèles IA.
- Fournir les CV certifiés de 2 ingénieurs Machine Learning seniors.
Pièces administratives obligatoires à joindre:
- Une caution bancaire provisoire de 5 000 TND.
- L'offre technique en 3 exemplaires.
- L'offre financière cachetée.
- Certificat d'immatriculation et quitus fiscal en règle.
"""

def main():
    print("=" * 80)
    print("  DEMO : RAW UNSTRUCTURED DATA  -->  UNIVERSAL JSON SCHEMA TRANSFORMER")
    print("=" * 80)

    print("\n[STEP 1] HERE IS THE RAW UNSTRUCTURED INPUT (Messy Text from PDF / Web):")
    print("-" * 80)
    print(RAW_UNSTRUCTURED_TEXT.strip())
    print("-" * 80)

    print("\n[STEP 2] PASSING THROUGH THE NVIDIA LLM TRANSFORMER PIPELINE...")
    print("-> Reading, extracting entities, structuring, and calibrating...")
    
    pipeline = get_pipeline()
    notice = pipeline.process(
        RAW_UNSTRUCTURED_TEXT,
        source_name="CERT Tender Portal",
        source_url="https://www.cert.nat.tn/tenders/2026-ai",
        persist_db=False,
    )

    print("\n[STEP 3] OUTPUT: STANDARDIZED UNIVERSAL JSON SCHEMA (ProcurementNotice):")
    print("=" * 80)
    
    # Export as clean indented JSON
    json_output = json.dumps(notice.model_dump(), indent=2, ensure_ascii=False)
    print(json_output)
    print("=" * 80)

    print("\n[KEY METRICS DETECTED]")
    print(f" • Subject / Objet    : {notice.objet}")
    print(f" • Organization       : {notice.organisme}")
    print(f" • Budget             : {notice.budget.formatted if notice.budget else 'N/A'}")
    print(f" • Deadline           : {notice.dates.submission_deadline}")
    print(f" • Number of Lots     : {len(notice.lots)}")
    print(f" • Required Documents : {len(notice.documents_requis)}")
    print(f" • Relevance Score    : {round(notice.relevance_score * 100, 1)}% (Pertinent: {notice.is_relevant})")
    print(f" • Recommendation     : {notice.analyse_faisabilite.recommandation if notice.analyse_faisabilite else 'N/A'}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
