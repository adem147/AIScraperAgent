from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Date, Float, Boolean, Text, JSON
from .db import Base


class BestApiEndpoint(Base):

    __tablename__ = "best_api_endpoints"

    id = Column(Integer, primary_key=True)

    source_id = Column(Integer, ForeignKey("sources.id"))

    url = Column(String)

    method = Column(String)

    similarity_score = Column(Float)


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)

    hash_id = Column(String, unique=True)

    title = Column(String)

    url = Column(String)

    type = Column(String)

    scrape_type = Column(String)


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)

    hash_id = Column(String, unique=True)

    source_id = Column(
        Integer,
        ForeignKey("sources.id")
    )

    title = Column(String)

    description = Column(String)

    url = Column(String)
    country = Column(String)

    published_date = Column(DateTime,index=True)

    submission_deadline = Column(DateTime,index=True)

    sector = Column(String)


class SimilarityResult(Base):
    __tablename__ = "similarity_results"

    id = Column(Integer, primary_key=True)

    opportunity_id = Column(
        Integer,
        ForeignKey("opportunities.id"),
        nullable=False,
        index=True,
    )

    similarity_score = Column(Float, nullable=False)

    title = Column(String, nullable=False)
