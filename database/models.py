from sqlalchemy import Column, ForeignKey, Integer, String, Date, Float, Boolean, Text, JSON
from .db import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_name = Column(String, nullable=True)
    url = Column(String, nullable=True)
    type = Column(String, nullable=True)
    scrape_type = Column(String, nullable=True)


class BestApiEndpoint(Base):
    __tablename__ = "best_api_endpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String, unique=True, index=True)
    endpoint_url = Column(String, nullable=False)
    method = Column(String, default="GET")
    similarity_score = Column(String, nullable=True)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    
    # Core fields
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    organization = Column(String, nullable=True)
    document_url = Column(String, nullable=True)
    submission_deadline = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    country = Column(String, nullable=True)
    language = Column(String, default="FR")
    
    # NLP Extracted Key Fields
    budget = Column(String, nullable=True)
    criteres = Column(JSON, nullable=True)
    lots = Column(JSON, nullable=True)
    documents_requis = Column(JSON, nullable=True)
    dates = Column(JSON, nullable=True)
    
    # Intelligence & Calibration
    relevance_score = Column(Float, nullable=True)
    is_relevant = Column(Boolean, default=False)
    relevance_rationale = Column(Text, nullable=True)
    
    # LLM Synthesis & Feasibility
    synthese_opportunite = Column(Text, nullable=True)
    analyse_faisabilite = Column(JSON, nullable=True)
    
    # Raw ingested data
    raw_data = Column(JSON, nullable=True)

