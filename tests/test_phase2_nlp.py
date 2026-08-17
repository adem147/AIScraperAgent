import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from LLM.nvidia_client import get_nvidia_client
from LLM.schemas import ProcurementNotice, DatesSchema, BudgetSchema, LotSchema, FeasibilityAnalysis
from LLM.nlp_extractor import NLPExtractor
from LLM.json_transformer import JSONTransformer
from LLM.relevance_scorer import RelevanceScorer
from LLM.feasibility_analyser import FeasibilityAnalyser
from LLM.pipeline import ProcurementIntelligencePipeline

CORPUS_PATH = Path(__file__).resolve().parent / "annotated_corpus.json"


class TestPhase2NLPExtractionEngine(unittest.TestCase):
    """Validation test suite for Phase 2 NLP, multilingual extraction, scoring calibration, and feasibility analysis."""

    @classmethod
    def setUpClass(cls):
        cls.client = get_nvidia_client()
        cls.extractor = NLPExtractor(client=cls.client)
        cls.transformer = JSONTransformer(client=cls.client)
        cls.scorer = RelevanceScorer(client=cls.client)
        cls.analyser = FeasibilityAnalyser(client=cls.client)
        cls.pipeline = ProcurementIntelligencePipeline()

        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            cls.corpus = json.load(f)

    def test_01_nvidia_client_connectivity(self):
        """Verify NVIDIA Build API connectivity with llama-3.1-8b-instruct."""
        res = self.client.generate_json("Output a json with key 'status' and value 'connected'")
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "connected")

    def test_02_french_nlp_extraction(self):
        """Test NLP extraction on French procurement notice (CERT SOC/AI)."""
        sample = next(item for item in self.corpus if item["id"] == "CORPUS-FR-01")
        notice = self.extractor.extract_from_text(sample["raw_text"], notice_id=sample["id"])

        self.assertEqual(notice.language, "FR")
        self.assertTrue(len(notice.objet) > 10, "Objet should be extracted")
        self.assertTrue("CERT" in notice.organisme or "Télécommunications" in notice.organisme or "Centre" in notice.organisme)
        
        # Check dates
        self.assertTrue(bool(notice.dates.submission_deadline), "Submission deadline should be extracted")
        self.assertTrue("2026" in str(notice.dates.submission_deadline))

        # Check lots
        self.assertTrue(len(notice.lots) >= 2, f"Expected 2 lots, got {len(notice.lots)}")

        # Check documents requis
        self.assertTrue(len(notice.documents_requis) >= 2, f"Expected required documents, got {notice.documents_requis}")

        # Check budget
        self.assertIsNotNone(notice.budget)
        self.assertTrue(notice.budget.amount is not None or notice.budget.formatted is not None)

    def test_03_english_nlp_extraction(self):
        """Test NLP extraction on English international procurement notice (World Bank AI Big Data)."""
        sample = next(item for item in self.corpus if item["id"] == "CORPUS-EN-02")
        notice = self.extractor.extract_from_text(sample["raw_text"], notice_id=sample["id"])

        self.assertEqual(notice.language, "EN")
        self.assertTrue("Data" in notice.objet or "Analytics" in notice.objet or "AI" in notice.objet)
        self.assertTrue("World Bank" in notice.organisme or "Ministry" in notice.organisme)
        self.assertTrue("2026" in str(notice.dates.submission_deadline))
        self.assertTrue(len(notice.criteres) > 0)
        self.assertTrue(len(notice.documents_requis) > 0)

    def test_04_arabic_nlp_extraction(self):
        """Test NLP extraction on Arabic procurement notice (Instance Nationale des Télécommunications 5G)."""
        sample = next(item for item in self.corpus if item["id"] == "CORPUS-AR-03")
        notice = self.extractor.extract_from_text(sample["raw_text"], notice_id=sample["id"])

        self.assertEqual(notice.language, "AR")
        self.assertTrue(len(notice.objet) > 5)
        self.assertTrue("الاتصالات" in notice.organisme or "الهيئة" in notice.organisme or "Télécommunications" in notice.organisme or len(notice.organisme) > 3)
        self.assertTrue("2026" in str(notice.dates.submission_deadline))
        self.assertTrue(len(notice.documents_requis) >= 1)

    def test_05_non_standard_json_transformation(self):
        """Test transforming arbitrary non-standard JSON into standardized ProcurementNotice."""
        sample = next(item for item in self.corpus if item["id"] == "CORPUS-NONSTD-JSON-05")
        notice = self.transformer.transform_json(sample["raw_json"], notice_id=sample["id"])

        self.assertIsInstance(notice, ProcurementNotice)
        self.assertTrue("Interoperability" in notice.objet or "Gateway" in notice.objet or "Procurement" in notice.objet)
        self.assertTrue("HAICOP" in notice.organisme or "Public Procurement" in notice.organisme or len(notice.organisme) > 3)
        self.assertTrue("2026-09-22" in str(notice.dates.submission_deadline))
        self.assertEqual(len(notice.lots), 2)
        self.assertTrue(len(notice.documents_requis) >= 2)

    def test_06_relevance_scoring_calibration(self):
        """Verify calibrated relevance scoring: >= 0.70 for IT/AI/Telecom notices, < 0.70 for civil engineering/roads."""
        # 1. Relevant French AI/SOC Notice
        fr_sample = next(item for item in self.corpus if item["id"] == "CORPUS-FR-01")
        fr_notice = self.extractor.extract_from_text(fr_sample["raw_text"])
        fr_evaluated = self.scorer.evaluate_notice(fr_notice)

        print(f"\n[CORPUS-FR-01] Score: {fr_evaluated.relevance_score} (is_relevant: {fr_evaluated.is_relevant})")
        print(f"Rationale: {fr_evaluated.relevance_rationale}")
        self.assertGreaterEqual(fr_evaluated.relevance_score, 0.70)
        self.assertTrue(fr_evaluated.is_relevant)

        # 2. Irrelevant Road Construction Notice
        road_sample = next(item for item in self.corpus if item["id"] == "CORPUS-IRRELEVANT-04")
        road_notice = self.extractor.extract_from_text(road_sample["raw_text"])
        road_evaluated = self.scorer.evaluate_notice(road_notice)

        print(f"\n[CORPUS-IRRELEVANT-04] Score: {road_evaluated.relevance_score} (is_relevant: {road_evaluated.is_relevant})")
        print(f"Rationale: {road_evaluated.relevance_rationale}")
        self.assertLess(road_evaluated.relevance_score, 0.70)
        self.assertFalse(road_evaluated.is_relevant)

    def test_07_feasibility_and_synthesis_generation(self):
        """Test generation of opportunity synthesis and preliminary feasibility analysis."""
        sample = next(item for item in self.corpus if item["id"] == "CORPUS-FR-01")
        notice = self.extractor.extract_from_text(sample["raw_text"])
        notice = self.scorer.evaluate_notice(notice)
        analyzed = self.analyser.analyze_opportunity(notice)

        self.assertIsNotNone(analyzed.synthese_opportunite)
        self.assertTrue(len(analyzed.synthese_opportunite) > 50)
        self.assertIsNotNone(analyzed.analyse_faisabilite)
        self.assertIn(analyzed.analyse_faisabilite.recommandation, ["GO", "A_ETUDIER_AVEC_PARTENAIRE"])
        self.assertTrue(len(analyzed.analyse_faisabilite.competences_requises) > 0)
        self.assertTrue(len(analyzed.analyse_faisabilite.risques_et_contraintes) > 0)

    def test_08_end_to_end_pipeline_and_database(self):
        """Test complete pipeline from raw unstructured input to database persistence."""
        sample = next(item for item in self.corpus if item["id"] == "CORPUS-EN-02")
        result = self.pipeline.process(
            sample["raw_text"],
            source_name="World Bank Test Feed",
            source_url="https://projects.worldbank.org/en/projects-operations/opportunities/WB-TEST-001",
            notice_id="WB-TEST-001",
            persist_db=True,
        )

        self.assertIsInstance(result, ProcurementNotice)
        self.assertGreaterEqual(result.relevance_score, 0.70)
        self.assertTrue(result.is_relevant)
        self.assertIsNotNone(result.synthese_opportunite)
        self.assertIsNotNone(result.analyse_faisabilite)


if __name__ == "__main__":
    unittest.main()
