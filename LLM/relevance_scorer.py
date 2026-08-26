import os
import json
from typing import Dict, Any, Optional, Tuple
from .nvidia_client import NvidiaLLMClient, get_nvidia_client
from .schemas import ProcurementNotice

try:
    from scraper.embedding import get_model
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:
    get_model = None
    cosine_similarity = None

RELEVANCE_THRESHOLD = 0.70

CERT_PROFILE_DESCRIPTION = (
    "Centre d'Études et de Recherche des Télécommunications (CERT) - Profile & Core Competencies:\n"
    "1. Artificial Intelligence & Machine Learning: NLP, LLM agents, computer vision, predictive analytics, data lakes.\n"
    "2. Cybersecurity & Trust: Security Operations Centers (SOC), SIEM, threat intelligence, vulnerability audits, ISO 27001.\n"
    "3. Telecommunications & Networks: 5G/4G, RF spectrum management, optical fiber, IoT, smart city networks, telecom regulation.\n"
    "4. Cloud & Software Engineering: Cloud migration, microservices, Kubernetes, enterprise web/mobile applications, DevOps.\n"
    "5. Digital Transformation: E-governance, digital health systems, interoperability, IT master plans and technical auditing."
)

RELEVANCE_EVALUATION_SYSTEM_PROMPT = f"""You are the Chief Technology Officer & Bid Evaluator at CERT (Centre d'Études et de Recherche des Télécommunications).
Your role is to strictly evaluate whether a public procurement notice / AMI matches the strategic domain and technical capabilities of CERT.

{CERT_PROFILE_DESCRIPTION}

Evaluation Rules:
1. Provide a 'relevance_score' between 0.0 and 1.0.
   - 0.80 - 1.00: Perfect match (e.g. AI/ML, SOC/Cybersecurity, Telecom network audit, Software platform, Cloud infrastructure).
   - 0.70 - 0.79: Strong match (e.g. IT modernization, digital health platform, data engineering, smart IoT systems).
   - 0.40 - 0.69: Partial or adjacent IT opportunity (e.g. general IT procurement, office automation, basic hardware).
   - 0.00 - 0.39: Irrelevant (e.g. Civil engineering, road construction, agriculture, water management, medical consumables, general logistics).
2. 'is_relevant' MUST be true IF AND ONLY IF relevance_score >= 0.70.
3. Provide a concise 'rationale' (1-2 sentences in French or English) explaining why the opportunity matches or does not match CERT.

Output strictly valid JSON conforming to:
{{
  "relevance_score": 0.85,
  "is_relevant": true,
  "rationale": "Direct alignment with CERT cybersecurity and SOC capabilities."
}}
"""


class RelevanceScorer:
    """Calibrated relevance scoring engine for CERT procurement opportunities (Threshold >= 70%)."""

    def __init__(self, client: Optional[NvidiaLLMClient] = None):
        self.client = client or get_nvidia_client()
        self.threshold = RELEVANCE_THRESHOLD

    def calculate_embedding_score(self, text: str) -> float:
        """Compute cosine similarity score against CERT domain profile."""
        if not text or get_model is None or cosine_similarity is None:
            return 0.50

        try:
            embed_model = get_model()
            profile_vec = embed_model.encode([CERT_PROFILE_DESCRIPTION])
            text_vec = embed_model.encode([text[:1000]])
            sim = cosine_similarity(profile_vec, text_vec)[0][0]
            # Normalize cosine similarity roughly from [-1, 1] / [0.2, 0.8] range into [0.0, 1.0]
            normalized = max(0.0, min(1.0, (sim - 0.1) / 0.7))
            return float(normalized)
        except Exception as e:
            print("Embedding calculation error:", e)
            return 0.50

    def evaluate_notice(self, notice: ProcurementNotice) -> ProcurementNotice:
        """Evaluate and calibrate relevance score for a ProcurementNotice."""
        text_context = (
            f"Titre/Objet: {notice.objet}\n"
            f"Organisme: {notice.organisme}\n"
            f"Secteur: {notice.sector or 'N/A'}\n"
            f"Pays: {notice.country or 'N/A'}\n"
            f"Critères: {', '.join(notice.criteres) if notice.criteres else 'N/A'}\n"
            f"Lots: {', '.join([l.title for l in notice.lots]) if notice.lots else 'N/A'}"
        )

        # 1. Embedding score
        emb_score = self.calculate_embedding_score(text_context)

        # 2. LLM alignment evaluation
        prompt = (
            f"Evaluate the relevance of the following procurement notice for CERT:\n\n"
            f"{text_context}\n"
        )

        try:
            llm_result = self.client.generate_json(
                prompt=prompt,
                system_prompt=RELEVANCE_EVALUATION_SYSTEM_PROMPT,
                max_tokens=512,
            )
            llm_score = float(llm_result.get("relevance_score", 0.5))
            rationale = llm_result.get("rationale") or "Évaluation automatique effectuée."
        except Exception as e:
            print("LLM relevance evaluation exception:", e)
            llm_score = emb_score
            rationale = "Score calculé par similarité sémantique."

        # 3. Calibrated combined score (60% LLM reasoning + 40% dense semantic embedding)
        calibrated_score = round(0.60 * llm_score + 0.40 * emb_score, 3)
        calibrated_score = max(0.0, min(1.0, calibrated_score))

        # Check threshold (70%)
        is_relevant = calibrated_score >= self.threshold

        notice.relevance_score = calibrated_score
        notice.is_relevant = is_relevant
        notice.relevance_rationale = rationale

        return notice
