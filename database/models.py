from sqlalchemy import Column, Integer, String, Date
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

    source_id = Column(Integer)

    title = Column(String)

    document_url = Column(String)

    submission_deadline = Column(Date)

    sector = Column(String)
