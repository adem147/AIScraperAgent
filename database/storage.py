from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import BestApiEndpoint, SimilarityResult, Source


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
    except Exception as e:
        session.rollback()
        print(e.text)
        return False
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
    except Exception as e:
        session.rollback()
        print(e)
        return False
    finally:
        session.close()


def save_similarity_results(results):
    """Replace the stored similarity results with the latest search results."""
    session: Session = SessionLocal()
    try:
        #session.query(SimilarityResult).delete()
        session.add_all(results)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(e)
        return False
    finally:
        session.close()
        
