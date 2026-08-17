from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class DatesSchema(BaseModel):
    publication_date: Optional[str] = Field(
        None, description="Date de publication de l'avis (format YYYY-MM-DD si possible)"
    )
    submission_deadline: Optional[str] = Field(
        None, description="Date et heure limite de remise des offres (format YYYY-MM-DD)"
    )
    opening_date: Optional[str] = Field(
        None, description="Date d'ouverture des plis"
    )
    clarification_deadline: Optional[str] = Field(
        None, description="Date limite de demande d'éclaircissements"
    )


class BudgetSchema(BaseModel):
    amount: Optional[float] = Field(
        None, description="Montant estimé ou alloué en valeur numérique"
    )
    currency: Optional[str] = Field(
        None, description="Devise (TND, EUR, USD, etc.)"
    )
    is_estimated: bool = Field(
        True, description="Vrai s'il s'agit d'une estimation indicative"
    )
    formatted: Optional[str] = Field(
        None, description="Représentation formatée (ex: 150 000 TND, 2.5M EUR)"
    )


class LotSchema(BaseModel):
    lot_number: Union[int, str] = Field(..., description="Numéro ou identifiant du lot")
    title: str = Field(..., description="Intitulé du lot")
    description: Optional[str] = Field(None, description="Description technique du lot")
    budget: Optional[str] = Field(None, description="Budget alloué au lot si spécifié")


class FeasibilityAnalysis(BaseModel):
    adequation_technique: str = Field(
        ..., description="Évaluation de l'alignement avec les compétences et activités du CERT"
    )
    competences_requises: List[str] = Field(
        default_factory=list,
        description="Liste des compétences et profils clés nécessaires pour soumissionner"
    )
    risques_et_contraintes: List[str] = Field(
        default_factory=list,
        description="Risques identifiés (délais, cautions bancaires, certifications, pénalités)"
    )
    recommandation: str = Field(
        ..., description="Recommandation préliminaire: 'GO', 'NO-GO' ou 'A_ETUDIER_AVEC_PARTENAIRE'"
    )
    score_faisabilite: float = Field(
        ..., ge=0.0, le=1.0, description="Score de faisabilité préliminaire (0.0 à 1.0)"
    )


class ProcurementNotice(BaseModel):
    id: Optional[str] = Field(None, description="Identifiant unique de l'opportunité")
    source: Optional[str] = Field(None, description="Portail ou source d'origine (ex: World Bank, TUNEPS, UN)")
    source_url: Optional[str] = Field(None, description="Lien direct vers l'avis ou document")
    language: str = Field("FR", description="Langue principale du document (FR, EN, AR)")
    
    # NLP Extracted Core Fields
    objet: str = Field(..., description="Objet ou titre complet de l'appel d'offres / AMI")
    organisme: str = Field(..., description="Organisme acheteur / Maître d'ouvrage")
    dates: DatesSchema = Field(default_factory=DatesSchema, description="Dates clés de la procédure")
    budget: Optional[BudgetSchema] = Field(None, description="Budget estimé et devise")
    criteres: List[str] = Field(default_factory=list, description="Critères d'éligibilité et de sélection")
    lots: List[LotSchema] = Field(default_factory=list, description="Allotissement / Détail des lots")
    documents_requis: List[str] = Field(default_factory=list, description="Documents administratifs et techniques exigés")
    
    # Classification & Context
    sector: Optional[str] = Field(None, description="Secteur d'activité principal")
    country: Optional[str] = Field(None, description="Pays ou région géographique")
    
    # Relevance Intelligence
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Score de pertinence calibré (0.0 à 1.0)")
    is_relevant: bool = Field(False, description="Vrai si relevance_score >= 0.70 (70%)")
    relevance_rationale: Optional[str] = Field(None, description="Justification du score de pertinence")
    
    # LLM Synthesis & Feasibility
    synthese_opportunite: Optional[str] = Field(None, description="Synthèse exécutive rédigée par le LLM")
    analyse_faisabilite: Optional[FeasibilityAnalysis] = Field(None, description="Analyse de faisabilité préliminaire")
    
    # Raw Data Payload
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Données brutes sources d'origine")

    def to_phase1_format(self) -> Dict[str, Any]:
        """Convert to legacy Phase 1 7-column dictionary format."""
        return {
            "title": self.objet,
            "description": self.synthese_opportunite or self.objet,
            "organization": self.organisme,
            "submission_deadline": self.dates.submission_deadline or "N/A",
            "country": self.country or "Global",
            "sector": self.sector or "Information Technology",
            "url": self.source_url or "",
            "score": round(self.relevance_score, 4),
        }
