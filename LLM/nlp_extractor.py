import json
from typing import Dict, Any, Optional, Union
from .nvidia_client import NvidiaLLMClient, get_nvidia_client
from .schemas import ProcurementNotice, DatesSchema, BudgetSchema, LotSchema


NLP_EXTRACTION_SYSTEM_PROMPT = """You are an expert Multilingual NLP Extraction Engine for Public Procurement Notices (AMI / Appels d'Offres) for CERT (Centre d'Études et de Recherche des Télécommunications).
Your job is to accurately extract structured procurement fields from text or document extracts in FRENCH (FR), ENGLISH (EN), and ARABIC (AR).

You MUST output ONLY a valid JSON object conforming EXACTLY to the following schema:
{
  "language": "FR | EN | AR",
  "objet": "Complete and clear title/subject of the tender/AMI",
  "organisme": "Issuing organization, ministry, or public authority",
  "dates": {
    "publication_date": "YYYY-MM-DD or string or null",
    "submission_deadline": "YYYY-MM-DD or string or null",
    "opening_date": "YYYY-MM-DD or string or null",
    "clarification_deadline": "YYYY-MM-DD or string or null"
  },
  "budget": {
    "amount": 150000.0 (or null if not specified),
    "currency": "TND | EUR | USD | etc. (or null)",
    "is_estimated": true,
    "formatted": "150,000 TND or null"
  },
  "criteres": [
    "Criterion 1 (e.g. Minimum 5 years experience)",
    "Criterion 2 (e.g. ISO 27001 certification)"
  ],
  "lots": [
    {
      "lot_number": 1,
      "title": "Lot title",
      "description": "Lot technical scope",
      "budget": "Lot budget if specified or null"
    }
  ],
  "documents_requis": [
    "Document 1 (e.g. Caution provisoire / Bid bond)",
    "Document 2 (e.g. Offre technique)",
    "Document 3 (e.g. Offre financière)",
    "Document 4 (e.g. Attestation fiscale / Quitus fiscal)"
  ],
  "sector": "Sector name (e.g. Télécommunications, Intelligence Artificielle, Cybersécurité, BTP, etc.)",
  "country": "Country name (e.g. Tunisie, France, Maroc, Global, etc.)"
}

Extraction Guidelines:
1. Multilingual Support: Process French, English, and Arabic texts accurately. Output extracted text clearly in the original or standardized language.
2. If certain fields (like budget or specific dates) are not explicitly mentioned in the text, set them to null or empty lists, do NOT invent facts.
3. If no lots are distinguished, provide a single lot representing the full scope or an empty list.
4. Output STRICT JSON only. Do not include markdown ticks, conversational text, or explanations.
"""


class NLPExtractor:
    """Multilingual NLP Extraction Module for Public Procurement Opportunities."""

    def __init__(self, client: Optional[NvidiaLLMClient] = None):
        self.client = client or get_nvidia_client()

    def extract_from_text(
        self,
        text: str,
        source_name: Optional[str] = None,
        source_url: Optional[str] = None,
        notice_id: Optional[str] = None,
    ) -> ProcurementNotice:
        """Extract structured procurement entities from raw unstructured document text."""
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty.")

        prompt = (
            f"Please extract all structured public procurement fields from the following notice text.\n\n"
            f"--- NOTICE TEXT START ---\n"
            f"{text.strip()[:6000]}\n"
            f"--- NOTICE TEXT END ---\n"
        )

        extracted_data = self.client.generate_json(
            prompt=prompt,
            system_prompt=NLP_EXTRACTION_SYSTEM_PROMPT,
            max_tokens=2048,
        )

        # Parse and build ProcurementNotice
        dates_raw = extracted_data.get("dates", {}) or {}
        dates = DatesSchema(
            publication_date=dates_raw.get("publication_date"),
            submission_deadline=dates_raw.get("submission_deadline"),
            opening_date=dates_raw.get("opening_date"),
            clarification_deadline=dates_raw.get("clarification_deadline"),
        )

        budget_raw = extracted_data.get("budget")
        budget = None
        if budget_raw and isinstance(budget_raw, dict) and any(budget_raw.values()):
            budget = BudgetSchema(
                amount=budget_raw.get("amount"),
                currency=budget_raw.get("currency"),
                is_estimated=budget_raw.get("is_estimated", True),
                formatted=budget_raw.get("formatted"),
            )

        lots_raw = extracted_data.get("lots", []) or []
        lots = []
        for l in lots_raw:
            if isinstance(l, dict) and "title" in l:
                lots.append(
                    LotSchema(
                        lot_number=l.get("lot_number", len(lots) + 1),
                        title=l.get("title", ""),
                        description=l.get("description"),
                        budget=l.get("budget"),
                    )
                )

        notice = ProcurementNotice(
            id=notice_id or extracted_data.get("id"),
            source=source_name or extracted_data.get("source", "Scraped Notice"),
            source_url=source_url or extracted_data.get("source_url"),
            language=extracted_data.get("language", "FR").upper(),
            objet=extracted_data.get("objet") or "Avis de marché public sans titre",
            organisme=extracted_data.get("organisme") or "Organisme public non précisé",
            dates=dates,
            budget=budget,
            criteres=extracted_data.get("criteres", []) or [],
            lots=lots,
            documents_requis=extracted_data.get("documents_requis", []) or [],
            sector=extracted_data.get("sector"),
            country=extracted_data.get("country"),
            raw_data={"source_text": text[:1000]},
        )

        return notice
