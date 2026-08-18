from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Date, Float, Boolean, Text, JSON
from .db import Base


class BestApiEndpoint(Base):

    __tablename__ = "best_api_endpoints"

    id = Column(Integer, primary_key=True)

    source_id = Column(Integer, ForeignKey("sources.id"))

    endpoint_url = Column(String)

    method = Column(String)

    similarity_score = Column(Float)


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)

    hash_id = Column(String, unique=True)

    organization_name = Column(String)

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

    document_url = Column(String)

    submission_deadline = Column(DateTime,index=True)

    sector = Column(String)
