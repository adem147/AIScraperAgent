"""Test script to process an opportunity notice and send the executive synthesis to sdiriaziz1999@gmail.com.

Usage:
    python test_email_synthesis.py
    python test_email_synthesis.py --to user@example.com
    python test_email_synthesis.py --mode digest
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from LLM import get_pipeline, get_email_service
from LLM.schemas import ProcurementNotice

SAMPLE_NOTICE_TEXT = """AVIS D'APPEL D'OFFRES NATIONAL N° 08/2026/CERT
Objet: Mise en place d'une plateforme de Security Operations Center (SOC) et d'un système d'analyse prédictive par Intelligence Artificielle pour la surveillance et la protection proactive des réseaux de télécommunications critiques.
Organisme acheteur: Centre d'Études et de Recherche des Télécommunications (CERT), Tunisie.
Dates clés:
- Date de publication: 2026-08-01
- Date limite de remise des offres: 2026-09-15 à 10h00
- Date d'ouverture des plis: 2026-09-15 à 11h00
Budget estimé: 450 000 TND TTC.
Allotissement:
- Lot 1: Fourniture, installation et configuration de la plateforme SIEM / SOC managé (Budget: 250 000 TND).
- Lot 2: Développement, intégration et déploiement de modèles de Machine Learning & Deep Learning pour la détection automatisée d'anomalies de trafic et de cyber-attaques en temps réel (Budget: 200 000 TND).
Critères d'éligibilité:
- Entreprise justifiant d'au moins 5 ans d'expérience avérée dans les projets SIEM, SOC et architectures télécoms.
- Présence d'au moins deux ingénieurs seniors certifiés en cybersécurité (CISSP, CEH) et d'un Lead Data Scientist IA.
Documents exigés:
- Cautionnement bancaire provisoire (4 500 TND).
- Cahier des charges paraphé et signé.
- Offre technique détaillée et bordereau des prix de l'offre financière.
- Quitus fiscal et attestation d'affiliation en règle à la CNSS.
Secteur: Télécommunications, Cybersécurité et Intelligence Artificielle.
Lien document: https://www.tuneps.tn/tender/CERT-SOC-AI-2026-08
"""

SAMPLE_NOTICE_TEXT_2 = """REQUEST FOR EXPRESSIONS OF INTEREST (CONSULTING SERVICES)
Project: World Bank African Digital Transformation & Data Intelligence Program
Assignment Title: Implementation of Enterprise AI Data Lakehouse and Real-Time Predictive Analytics Platform for Public Finance & Automated Procurement Auditing.
Issuing Organization: World Bank / Regional Economic Development Authority
Country: Regional / Multi-Country
Key Dates:
- Publication Date: 2026-08-05
- Submission Deadline Date: 2026-09-30 at 17:00 UTC
Estimated Budget: USD 350,000
Lots: Single Comprehensive Lot covering Cloud Infrastructure, Data Ingestion Pipelines, LLM Search Agents, and BI Dashboards.
Qualification Criteria:
- Proven track record with at least 3 completed enterprise data science / machine learning deployments in the last 4 years.
- Key personnel must include a Lead Cloud Architect, Senior AI/NLP Engineer, and Cybersecurity Auditor.
Required Documents:
- Letter of Expression of Interest
- Audited financial statements for the past 3 fiscal years
- CVs of key expert personnel
- ISO 27001 / SOC 2 certification
Source Link: https://projects.worldbank.org/en/projects-operations/opportunities/WB-AI-LAKE-2026
"""


def run_test(recipient: str, mode: str = "single"):
    print("=" * 75, flush=True)
    print("  AIScraperAgent - Test d'Envoi des Synthèses par Email", flush=True)
    print("=" * 75, flush=True)
    print(f"📧 Destinataire cible : {recipient}", flush=True)
    print(f"🔧 Mode               : {mode.upper()}", flush=True)
    print("-" * 75, flush=True)

    # 1. Test SMTP Connection
    email_service = get_email_service()
    print("\n[1/3] Vérification de la connexion SMTP...", flush=True)
    print(f"      Serveur SMTP : {email_service.smtp_server}:{email_service.smtp_port}", flush=True)
    print(f"      Utilisateur  : {email_service.smtp_user}", flush=True)
    print(f"      Expéditeur   : {email_service.sender_email}", flush=True)
    
    success, msg = email_service.test_connection()
    if success:
        print(f"      ✅ {msg}", flush=True)
    else:
        print(f"      ❌ Échec de la connexion SMTP : {msg}", flush=True)
        print("      ⚠️ Veuillez vérifier les variables SMTP dans .env (SMTP_USER, SMTP_PASSWORD).", flush=True)
        return False

    # 2. Run Pipeline to extract notice, calculate relevance, generate synthesis & feasibility
    pipeline = get_pipeline()
    print("\n[2/3] Traitement de l'opportunité dans le pipeline IA (NVIDIA LLM)...", flush=True)
    
    if mode == "single":
        notice = pipeline.process(
            raw_input=SAMPLE_NOTICE_TEXT,
            source_name="TUNEPS / CERT Portal",
            source_url="https://www.tuneps.tn/tender/CERT-SOC-AI-2026-08",
            notice_id="CERT-SOC-AI-2026-08",
            persist_db=True,
            send_email=False,
        )

        print(f"      📌 Objet         : {notice.objet}", flush=True)
        print(f"      🏢 Organisme     : {notice.organisme}", flush=True)
        print(f"      🎯 Score         : {round(notice.relevance_score * 100, 1)}% (Pertinent: {notice.is_relevant})", flush=True)
        if notice.analyse_faisabilite:
            print(f"      🧠 Recommandation: {notice.analyse_faisabilite.recommandation}", flush=True)
        print(f"      📝 Synthèse (aperçu) :\n         {notice.synthese_opportunite[:200]}...", flush=True)

        # 3. Send Email
        print(f"\n[3/3] Envoi de l'email de synthèse à <{recipient}>...", flush=True)
        sent = pipeline.send_synthesis_email(notice, recipient_email=recipient)
        if sent:
            print(f"\n🎉 SUCCÈS ! L'email de synthèse a été envoyé avec succès à <{recipient}>.", flush=True)
            print("   Consultez votre boîte de réception (et vos spams au cas où) !", flush=True)
            return True
        else:
            print(f"\n❌ Échec de l'envoi de l'email à <{recipient}>.", flush=True)
            return False

    elif mode == "digest":
        print("      Traitement du lot d'opportunités...", flush=True)
        notice1 = pipeline.process(SAMPLE_NOTICE_TEXT, source_name="TUNEPS", persist_db=True)
        notice2 = pipeline.process(SAMPLE_NOTICE_TEXT_2, source_name="World Bank", persist_db=True)
        notices = [notice1, notice2]

        print(f"\n[3/3] Envoi du digest ({len(notices)} opportunités) à <{recipient}>...", flush=True)
        sent = pipeline.send_batch_synthesis_email(
            notices=notices,
            recipient_email=recipient,
            digest_title="Rapport Hebdomadaire des Opportunités Télécoms & IA",
        )
        if sent:
            print(f"\n🎉 SUCCÈS ! Le digest a été envoyé avec succès à <{recipient}>.", flush=True)
            return True
        else:
            print(f"\n❌ Échec de l'envoi du digest à <{recipient}>.", flush=True)
            return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Envoyer les synthèses d'opportunités par email.")
    parser.add_argument(
        "--to",
        type=str,
        default="sdiriaziz1999@gmail.com",
        help="Adresse email du destinataire (défaut: sdiriaziz1999@gmail.com)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["single", "digest"],
        default="single",
        help="Type d'envoi: 'single' (synthèse détaillée) ou 'digest' (rapport multi-opportunités)",
    )
    args = parser.parse_args()

    run_test(recipient=args.to, mode=args.mode)
