from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Date, Float, Boolean, Text, JSON
from .db import Base


class BestApiEndpoint(Base):
    __tablename__ = "best_api_endpoints"

    id = Column(Integer, primary_key=True)
    source_url = Column(String, nullable=True)
    endpoint_url = Column(String, nullable=True)
    method = Column(String, nullable=True)
    similarity_score = Column(String, nullable=True)

    def __init__(self, **kwargs):
        if "url" in kwargs and "endpoint_url" not in kwargs:
            kwargs["endpoint_url"] = kwargs.pop("url")
        if "header" in kwargs:
            kwargs.pop("header")
        if "payload" in kwargs:
            kwargs.pop("payload")
        if "source_id" in kwargs:
            kwargs.pop("source_id")
        super().__init__(**kwargs)

    @property
    def url(self):
        return self.endpoint_url

    @url.setter
    def url(self, value):
        self.endpoint_url = value


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    organization_name = Column(String, nullable=True)
    url = Column(String, nullable=True)
    type = Column(String, nullable=True)
    scrape_type = Column(String, nullable=True)

    def __init__(self, **kwargs):
        if "title" in kwargs and "organization_name" not in kwargs:
            kwargs["organization_name"] = kwargs.pop("title")
        if "hash_id" in kwargs:
            kwargs.pop("hash_id")
        super().__init__(**kwargs)

    @property
    def title(self):
        return self.organization_name or "Source"

    @title.setter
    def title(self, value):
        self.organization_name = value


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)
    hash_id = Column(String, unique=True, nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    organization = Column(String, nullable=True)
    document_url = Column(String, nullable=True)
    submission_deadline = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    country = Column(String, nullable=True)
    language = Column(String, nullable=True)
    budget = Column(String, nullable=True)
    criteres = Column(JSON, nullable=True)
    lots = Column(JSON, nullable=True)
    documents_requis = Column(JSON, nullable=True)
    dates = Column(JSON, nullable=True)
    relevance_score = Column(Float, nullable=True)
    is_relevant = Column(Boolean, nullable=True)
    relevance_rationale = Column(Text, nullable=True)
    synthese_opportunite = Column(Text, nullable=True)
    analyse_faisabilite = Column(JSON, nullable=True)
    raw_data = Column(JSON, nullable=True)

    def __init__(self, **kwargs):
        if "url" in kwargs and "document_url" not in kwargs:
            kwargs["document_url"] = kwargs.pop("url")
        if "published_date" in kwargs:
            pub_date = kwargs.pop("published_date")
            if pub_date and "dates" not in kwargs:
                kwargs["dates"] = {"published_date": str(pub_date)}
        # convert dates to string if datetime
        if "submission_deadline" in kwargs and kwargs["submission_deadline"] is not None:
            kwargs["submission_deadline"] = str(kwargs["submission_deadline"])
        super().__init__(**kwargs)

    @property
    def url(self):
        return self.document_url

    @url.setter
    def url(self, value):
        self.document_url = value


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
