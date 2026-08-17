import json
from typing import Dict, Any, Optional, Union
from .nvidia_client import NvidiaLLMClient, get_nvidia_client
from .schemas import ProcurementNotice, DatesSchema, BudgetSchema, LotSchema


JSON_TRANSFORMATION_SYSTEM_PROMPT = """You are an expert JSON Transformer & Schema Normalizer for Public Procurement Intelligence at CERT.
Your job is to take an incoming HETEROGENEOUS, NON-STANDARD, OR ARBITRARY JSON payload representing a public procurement notice, expression of interest (AMI), or tender, and transform it into the standardized CERT ProcurementNotice JSON format.

Target Standardized Output Format:
{
  "language": "FR | EN | AR",
  "objet": "Standardized title / subject of the procurement notice",
  "organisme": "Standardized issuing organization / authority / buyer",
  "dates": {
    "publication_date": "YYYY-MM-DD or null",
    "submission_deadline": "YYYY-MM-DD or null",
    "opening_date": "YYYY-MM-DD or null",
    "clarification_deadline": "YYYY-MM-DD or null"
  },
  "budget": {
    "amount": 100000.0 or null,
    "currency": "TND | EUR | USD | etc. or null",
    "is_estimated": true,
    "formatted": "100,000 EUR or null"
  },
  "criteres": [
    "Extracted or inferred eligibility and selection criteria"
  ],
  "lots": [
    {
      "lot_number": 1,
      "title": "Lot title",
      "description": "Lot scope",
      "budget": "Lot budget or null"
    }
  ],
  "documents_requis": [
    "List of required submission documents"
  ],
  "sector": "Normalized sector (e.g. Information & Communications Technologies, Cyber Security, Cloud, etc.)",
  "country": "Country name"
}

Transformation Rules:
1. Harmonize messy key names (e.g., 'bid_description', 'project_name', 'titre', 'desc', 'descr', 'nom_acheteur', 'closing_date', 'ddv', 'subm_date', etc.) into standard fields.
2. If fields like budget, lots, or required documents are mentioned inside descriptions or nested dictionaries, extract them into their respective fields.
3. If not specified in the input JSON, set to null or empty list.
4. Output STRICT JSON only without any markdown ticks or explanations.
"""


class JSONTransformer:
    """Transforms arbitrary / non-standard JSON payloads into standardized ProcurementNotice schemas."""

    def __init__(self, client: Optional[NvidiaLLMClient] = None):
        self.client = client or get_nvidia_client()

    def transform_json(
        self,
        raw_json: Union[Dict[str, Any], str],
        source_name: Optional[str] = None,
        source_url: Optional[str] = None,
        notice_id: Optional[str] = None,
    ) -> ProcurementNotice:
        """Transform non-standard JSON into standardized ProcurementNotice."""
        if isinstance(raw_json, str):
            try:
                parsed_json = json.loads(raw_json)
            except Exception:
                parsed_json = {"raw_text": raw_json}
        elif isinstance(raw_json, dict):
            parsed_json = raw_json
        else:
            raise TypeError("raw_json must be a dict or a valid JSON string.")

        json_str = json.dumps(parsed_json, ensure_ascii=False, indent=2)

        prompt = (
            f"Transform the following arbitrary incoming JSON into the standardized CERT ProcurementNotice format:\n\n"
            f"```json\n{json_str[:5000]}\n```"
        )

        extracted_data = self.client.generate_json(
            prompt=prompt,
            system_prompt=JSON_TRANSFORMATION_SYSTEM_PROMPT,
            max_tokens=2048,
        )

        # Fallback to heuristic mapping if LLM returned empty dict
        if not extracted_data:
            extracted_data = self._heuristic_fallback(parsed_json)

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

        notice_identifier = (
            notice_id
            or extracted_data.get("id")
            or parsed_json.get("id")
            or parsed_json.get("project_id")
            or parsed_json.get("notice_id")
        )

        notice = ProcurementNotice(
            id=str(notice_identifier) if notice_identifier else None,
            source=source_name or extracted_data.get("source") or parsed_json.get("source", "Standardized JSON Source"),
            source_url=source_url or extracted_data.get("source_url") or parsed_json.get("url") or parsed_json.get("document_url"),
            language=extracted_data.get("language", "FR").upper(),
            objet=extracted_data.get("objet") or parsed_json.get("title") or parsed_json.get("project_name") or "Avis de marché",
            organisme=extracted_data.get("organisme") or parsed_json.get("organization") or parsed_json.get("buyer") or "Organisme public",
            dates=dates,
            budget=budget,
            criteres=extracted_data.get("criteres", []) or [],
            lots=lots,
            documents_requis=extracted_data.get("documents_requis", []) or [],
            sector=extracted_data.get("sector") or parsed_json.get("sector"),
            country=extracted_data.get("country") or parsed_json.get("country"),
            raw_data=parsed_json,
        )

        return notice

    def _heuristic_fallback(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Simple heuristic extraction when LLM is unavailable or offline."""
        title = raw.get("title") or raw.get("project_name") or raw.get("objet") or raw.get("subject") or ""
        desc = raw.get("description") or raw.get("bid_description") or raw.get("descr") or ""
        org = raw.get("organization") or raw.get("organisme") or raw.get("buyer") or raw.get("project_ctry_name") or ""
        deadline = raw.get("submission_deadline") or raw.get("submission_deadline_date") or raw.get("date_limite") or ""
        country = raw.get("country") or raw.get("project_ctry_name") or raw.get("pays") or ""
        sector = raw.get("sector") or raw.get("procurement_major_sector_name") or ""

        return {
            "language": "FR",
            "objet": title or desc[:80],
            "organisme": org,
            "dates": {"submission_deadline": deadline},
            "sector": sector,
            "country": country,
            "criteres": [],
            "lots": [],
            "documents_requis": [],
        }
