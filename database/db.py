from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(
    "sqlite:///CERT.db"
)

SessionLocal = sessionmaker(
    bind=engine
)

Base = declarative_base()

from database.models import Opportunity
from scraper.hashing import generate_hash


def parse_datetime(value):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            return None

        try:
            return datetime.fromisoformat(normalized_value.replace("Z", "+00:00"))
        except ValueError:
            for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(normalized_value, date_format)
                except ValueError:
                    continue

    raise ValueError(f"Unsupported datetime value: {value!r}")


def insert_opportunities(session, source, dataframe):
    """Insert one scraper's filtered DataFrame as a separate batch."""
    opportunities = []

    for item in dataframe.to_dict(orient="records"):
        try:
            published_date = parse_datetime(item.get("published_date"))
            submission_deadline = parse_datetime(item.get("submission_deadline"))

            opportunity = Opportunity(
                source_id=source.id,
                title=item.get("title", ""),
                description=item.get("description", ""),
                url=item.get("url", ""),
                published_date=published_date,
                submission_deadline=submission_deadline,
                sector=item.get("sector", ""),
                hash_id=generate_hash(
                    item.get("title", ""),
                    submission_deadline.isoformat() if submission_deadline else "",
                    item.get("description", ""),
                ),
            )

            session.add(opportunity)
            session.commit()
            opportunities.append(opportunity)

        except Exception:
            session.rollback()

    return opportunities