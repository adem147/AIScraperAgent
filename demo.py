"""Interactive CLI Demo for Phase 2 NLP Extraction, Relevance Scoring, and Feasibility Analysis.
Run with: python demo.py
"""

import os
import sys
import json
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from LLM import get_pipeline, JSONTransformer

SAMPLE_NOTICES = {
    "1": {
        "title": "French Tender: CERT AI & Security Operations Center (SOC)",
        "text": """AVIS D'APPEL D'OFFRES NATIONAL N° 08/2026/CERT
Objet: Mise en place d'une plateforme de Security Operations Center (SOC) et d'un système d'analyse prédictive par Intelligence Artificielle pour la surveillance des réseaux télécoms nationaux.
Organisme acheteur: Centre d'Études et de Recherche des Télécommunications (CERT), Tunisie.
Dates clés:
- Date de publication: 2026-08-01
- Date limite de remise des offres: 2026-09-15 à 10h00
- Date d'ouverture des plis: 2026-09-15 à 11h00
Budget estimé: 450 000 TND TTC.
Allotissement:
- Lot 1: Fourniture, installation et configuration de la solution SIEM / SOC (Budget: 250 000 TND).
- Lot 2: Développement et déploiement des modèles d'IA pour la détection automatisée d'anomalies de trafic (Budget: 200 000 TND).
Critères d'éligibilité:
- Entreprise justifiant d'au moins 5 ans d'expérience dans les projets SIEM et télécoms.
- Présence d'au moins deux ingénieurs certifiés en cybersécurité (CISSP, CEH).
Documents exigés:
- Cautionnement provisoire (4 500 TND).
- Cahier des charges paraphé et signé.
- Offre technique détaillée et offre financière.
- Quitus fiscal et attestation d'affiliation à la CNSS.
Secteur: Télécommunications et Cybersécurité."""
    },
    "2": {
        "title": "English Tender: World Bank Cloud Big Data Lake & AI",
        "text": """REQUEST FOR EXPRESSIONS OF INTEREST
Project: World Bank Digital Transformation and Data Intelligence Initiative
Assignment Title: Consulting Services for the Development of an AI-Powered Big Data Lake and Predictive Analytics Platform for Public Services.
Issuing Organization: World Bank & Ministry of Digital Economy
Country: Regional / Multi-Country
Key Dates:
- Publication Date: 2026-08-05
- Submission Deadline Date: 2026-09-30 at 17:00 UTC
Estimated Budget: USD 350,000
Lots: Single Comprehensive Lot covering Architecture, ETL Data Pipeline, Machine Learning Models, and Cloud DevOps Deployment.
Qualification Criteria:
- Proven track record with at least 3 completed enterprise data science / machine learning projects in the last 4 years.
- Key personnel must include a Lead Data Architect, Senior Machine Learning Engineer, and Cloud Security Specialist.
Required Documents:
- Letter of Expression of Interest
- Corporate profile and audited financial statements for the past 3 fiscal years
- CVs of proposed key experts
- ISO 27001 certification"""
    },
    "3": {
        "title": "Arabic Tender: Instance Nationale des Télécommunications (5G QoE)",
        "text": """إعلان طلب عروض عدد 14/2026
الموضوع: اقتناء وتركيز منظومة معلوماتية ذكية لمراقبة جودة خدمات شبكات الاتصالات المتنقلة والجيل الخامس (5G QoE Monitoring System) وتحليل البيانات الضخمة.
المشتري العمومي: الهيئة الوطنية للاتصالات، تونس.
الآجال والتواريخ:
- تاريخ النشر: 2026-08-02
- التاريخ الأقصى لقبول العروض: 2026-09-25 على الساعة 11:00 صباحا
- تاريخ فتح العروض: 2026-09-25 على الساعة 11:30 صباحا
الميزانية التقديرية: 320,000 دينار تونسي
الشروط والمعايير:
- أقدمية لا تقل عن 3 سنوات في مجال الشبكات وهندسة البرمجيات
- توفير فريق عمل يضم مهندسي اتصالات وبرمجيات معتمدين
الوثائق المطلوبة:
- الضمان المالي الوقتي (الضمانة البنكية)
- العرض الفني الكامل والعرض المالي
- شهادة الوضعية الجبائية والشهادة في عدم الإفلاس"""
    },
    "4": {
        "title": "Irrelevant Notice (Control): Road Construction (BTP)",
        "text": """INVITATION FOR BIDS (CIVIL WORKS)
Contract Title: Construction of 75 km Heavy Gravel Roads, Culverts, and Concrete Bridges in Zambezia Province.
Employer: National Road Authority / Department of Rural Public Infrastructure
Submission Deadline: 2026-09-10
Estimated Budget: USD 1,800,000
Scope: Excavation, asphalt paving, earthworks, drainage trenches, and safety barrier installation.
Required: Heavy construction equipment fleet (graders, bulldozers, dump trucks) and civil engineering civil works license."""
    }
}


def print_notice_summary(notice):
    print("\n" + "=" * 70)
    print(" 🚀 RESULTAT DE L'EXTRACTION NLP & ANALYSE DE L'OPPORTUNITE")
    print("=" * 70)
    print(f"📌 OBJET / TITRE     : {notice.objet}")
    print(f"🏢 ORGANISME         : {notice.organisme}")
    print(f"🌐 LANGUE / PAYS     : {notice.language} / {notice.country or 'N/A'}")
    print(f"📂 SECTEUR           : {notice.sector or 'N/A'}")
    print(f"📅 DATE LIMITE       : {notice.dates.submission_deadline or 'N/A'}")
    
    budget_str = notice.budget.formatted if notice.budget else "Non spécifié"
    print(f"💰 BUDGET ESTIMÉ     : {budget_str}")

    print("\n📦 LOTS IDENTIFIÉS :")
    if notice.lots:
        for lot in notice.lots:
            b = f" (Budget: {lot.budget})" if lot.budget else ""
            print(f"   • Lot {lot.lot_number}: {lot.title}{b}")
    else:
        print("   • Lot unique / Non alloti")

    print("\n📋 CRITÈRES D'ÉLIGIBILITÉ :")
    if notice.criteres:
        for crit in notice.criteres:
            print(f"   • {crit}")
    else:
        print("   • Non spécifiés explicitement")

    print("\n📑 DOCUMENTS EXIGÉS :")
    if notice.documents_requis:
        for doc in notice.documents_requis:
            print(f"   • {doc}")
    else:
        print("   • Documents usuels de soumission")

    print("\n" + "-" * 70)
    score_pct = round(notice.relevance_score * 100, 1)
    status_icon = "✅ PERTINENT (Seuil ≥ 70%)" if notice.is_relevant else "❌ NON PERTINENT (< 70%)"
    print(f"🎯 SCORE DE PERTINENCE : {score_pct}%  -->  {status_icon}")
    if notice.relevance_rationale:
        print(f"💡 JUSTIFICATION       : {notice.relevance_rationale}")

    if notice.analyse_faisabilite:
        print("\n🧠 ANALYSE DE FAISABILITÉ PRÉLIMINAIRE :")
        print(f"   • Recommandation      : {notice.analyse_faisabilite.recommandation}")
        print(f"   • Adéquation Tech     : {notice.analyse_faisabilite.adequation_technique}")
        print(f"   • Compétences clés    : {', '.join(notice.analyse_faisabilite.competences_requises)}")
        print(f"   • Risques identifiés  : {', '.join(notice.analyse_faisabilite.risques_et_contraintes)}")

    if notice.synthese_opportunite:
        print("\n📝 SYNTHÈSE EXÉCUTIVE :")
        print(f"{notice.synthese_opportunite}")
    print("=" * 70 + "\n")


def main():
    pipeline = get_pipeline()

    print("\n" + "#" * 70)
    print("  AIScraperAgent - Test Console (NVIDIA Build API & NLP Extraction)")
    print("#" * 70)
    print("Choisissez une option :")
    print(" [1] Tester l'avis Français (CERT SOC / IA)")
    print(" [2] Tester l'avis Anglais (World Bank Cloud & Big Data)")
    print(" [3] Tester l'avis Arabe (الهيئة الوطنية للاتصالات 5G)")
    print(" [4] Tester l'avis Non-Pertinent (Génie Civil / Routes)")
    print(" [5] Tester la transformation d'un JSON non standard (World Bank API format)")
    print(" [6] Saisir ou coller votre propre texte d'appel d'offres")
    print(" [q] Quitter")
    print("-" * 70)

    choice = input("Votre choix [1-6, q]: ").strip()

    if choice in SAMPLE_NOTICES:
        sample = SAMPLE_NOTICES[choice]
        print(f"\nTraitement de : {sample['title']}...")
        notice = pipeline.process(sample["text"], persist_db=True)
        print_notice_summary(notice)

    elif choice == "5":
        print("\nTransformation d'un JSON brut avec des clés arbitraires...")
        raw_json = {
            "notice_type": "Request for Proposals",
            "project_name": "Digital Public Procurement Interoperability & API Gateway",
            "bid_description": "Selection of software firm to build microservices, REST APIs, OAuth2 security and automated document validation workflows.",
            "project_ctry_name": "Tunisia",
            "procurement_major_sector_name": "Information and Communications Technologies",
            "submission_deadline_date": "2026-09-22T14:00:00Z",
            "buyer": "High Authority of Public Procurement (HAICOP)",
            "estimated_cost": "180000 EUR",
            "lots_info": [
                {"num": 1, "name": "API Gateway and Auth Subsystem", "amt": "100k EUR"},
                {"num": 2, "name": "Automated Document Validation Module", "amt": "80k EUR"}
            ],
            "mandatory_docs": [
                "Technical proposal",
                "Financial cost breakdown",
                "Company registration certificate",
                "Bid security bond"
            ]
        }
        notice = pipeline.process(raw_json, persist_db=True)
        print_notice_summary(notice)

    elif choice == "6":
        print("\nCollez votre texte d'avis ci-dessous (Appuyez sur Entrée deux fois quand vous avez terminé) :")
        lines = []
        while True:
            try:
                line = input()
                if not line and lines and not lines[-1]:
                    break
                lines.append(line)
            except EOFError:
                break
        user_text = "\n".join(lines).strip()
        if user_text:
            print("\nAnalyse en cours via NVIDIA LLM...")
            notice = pipeline.process(user_text, persist_db=True)
            print_notice_summary(notice)
        else:
            print("Texte vide. Annulation.")

    elif choice.lower() == "q":
        print("Au revoir!")
        return
    else:
        print("Option invalide.")


if __name__ == "__main__":
    main()
