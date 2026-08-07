from sqlalchemy import Column, ForeignKey, Integer, String, Date
from .db import Base


class Source(Base):

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)

    organization_name = Column(String)

    url = Column(String)

    type = Column(String)

    scrape_type = Column(String)


class Opportunity(Base):

    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)

    source_id = Column(
        Integer,
        ForeignKey("sources.id")
    )

    title = Column(String)

    description = Column(String)

    document_url = Column(String)

    submission_deadline = Column(String)

    sector = Column(String)
