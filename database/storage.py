from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import BestApiEndpoint, Source


def get_all_sources():
    """Retrieve all sources from the database."""
    session: Session = SessionLocal()
    try:
        return session.query(Source).all()
    finally:
        session.close()

def get_best_api_for_source(source_id):
    """Retrieve the best API endpoint for a given source ID."""
    session: Session = SessionLocal()
    try:
        return (
            session.query(BestApiEndpoint)
            .filter(BestApiEndpoint.source_id == source_id)
            .first()
        )
    finally:
        session.close()

def save_best_api_for_source(best_api_endpoint: BestApiEndpoint):
    """Persist the best API endpoint for a website, only once per source ID."""
    session: Session = SessionLocal()
    try:
        session.add(
            best_api_endpoint
        )
        session.commit()
        return True
    finally:
        session.close()
