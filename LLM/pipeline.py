import json
from typing import Dict, Any, Union, Optional, List
import pandas as pd

from .schemas import ProcurementNotice
from .nlp_extractor import NLPExtractor
from .json_transformer import JSONTransformer
from .relevance_scorer import RelevanceScorer
from .feasibility_analyser import FeasibilityAnalyser
from .nvidia_client import get_nvidia_client

from database.storage import initialize_database, save_procurement_notice
from qdrant_embedding import store_ami_embedding


class ProcurementIntelligencePipeline:
    """Unified Phase 2 Pipeline for Ingestion, NLP Extraction, Relevance Scoring, Feasibility, and Storage."""

    def __init__(self):
        client = get_nvidia_client()
        self.extractor = NLPExtractor(client=client)
        self.transformer = JSONTransformer(client=client)
        self.scorer = RelevanceScorer(client=client)
        self.analyser = FeasibilityAnalyser(client=client)
        
        # Ensure database tables exist
        try:
            initialize_database()
        except Exception as e:
            print("Database table initialization info:", e)

    def process(
        self,
        raw_input: Union[str, Dict[str, Any], pd.Series],
        source_name: Optional[str] = None,
        source_url: Optional[str] = None,
        notice_id: Optional[str] = None,
        persist_db: bool = True,
    ) -> ProcurementNotice:
        """Process any raw notice (text string, JSON dict, or pandas series) through the complete AI pipeline."""
        
        # Step 1: Extraction / Transformation
        if isinstance(raw_input, pd.Series):
            raw_dict = raw_input.to_dict()
            notice = self.transformer.transform_json(
                raw_json=raw_dict,
                source_name=source_name,
                source_url=source_url,
                notice_id=notice_id,
            )
        elif isinstance(raw_input, dict):
            notice = self.transformer.transform_json(
                raw_json=raw_input,
                source_name=source_name,
                source_url=source_url,
                notice_id=notice_id,
            )
        elif isinstance(raw_input, str):
            # If string is valid JSON dict, use transformer, otherwise use text NLP extractor
            stripped = raw_input.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    parsed = json.loads(stripped)
                    notice = self.transformer.transform_json(
                        raw_json=parsed,
                        source_name=source_name,
                        source_url=source_url,
                        notice_id=notice_id,
                    )
                except Exception:
                    notice = self.extractor.extract_from_text(
                        text=raw_input,
                        source_name=source_name,
                        source_url=source_url,
                        notice_id=notice_id,
                    )
            else:
                notice = self.extractor.extract_from_text(
                    text=raw_input,
                    source_name=source_name,
                    source_url=source_url,
                    notice_id=notice_id,
                )
        else:
            raise TypeError(f"Unsupported input type: {type(raw_input)}")

        # Step 2: Relevance Calibration (Threshold >= 70%)
        notice = self.scorer.evaluate_notice(notice)

        # Step 3: Executive Synthesis & Preliminary Feasibility Analysis
        notice = self.analyser.analyze_opportunity(notice)

        # Step 4: Database Persistence
        if persist_db:
            self.save_to_database(notice)

        return notice

    def process_batch(
        self,
        items: List[Union[str, Dict[str, Any]]],
        persist_db: bool = True,
    ) -> List[ProcurementNotice]:
        """Process a list of notices sequentially."""
        results = []
        for item in items:
            try:
                res = self.process(item, persist_db=persist_db)
                results.append(res)
            except Exception as e:
                print(f"Error processing item: {e}")
        return results

    def save_to_database(self, notice: ProcurementNotice) -> Optional[int]:
        """Save the processed notice through the database storage layer."""
        try:
            return save_procurement_notice(notice)
        except Exception as e:
            print("Database persistence error:", e)
            return None


# Singleton pipeline instance
_pipeline: Optional[ProcurementIntelligencePipeline] = None

def get_pipeline() -> ProcurementIntelligencePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ProcurementIntelligencePipeline()
    return _pipeline
