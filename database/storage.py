from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import BestApiEndpoint, Opportunity, SimilarityResult, Source


def get_all_sources():
    """Retrieve all sources from the database."""
    session: Session = SessionLocal()
    try:
        return session.query(Source).all()
    finally:
        session.close()


def get_sources_by_ids(source_ids):
    """Retrieve source records needed to label Qdrant results."""
    source_ids = {source_id for source_id in source_ids if source_id is not None}
    if not source_ids:
        return {}

    session: Session = SessionLocal()
    try:
        return {
            source.id: source
            for source in session.query(Source).filter(Source.id.in_(source_ids)).all()
        }
    finally:
        session.close()


def count_opportunities():
    """Return the number of stored opportunities."""
    session: Session = SessionLocal()
    try:
        return session.query(Opportunity).count()
    finally:
        session.close()


def search_opportunities(query="", source_id=None):
    """Find opportunities matching text and, optionally, a source."""
    session: Session = SessionLocal()
    try:
        opportunity_query = session.query(Opportunity, Source).outerjoin(
            Source, Opportunity.source_id == Source.id
        )
        if source_id is not None:
            opportunity_query = opportunity_query.filter(Opportunity.source_id == source_id)

        terms = {term.lower() for term in query.split() if term.strip()}
        results = []
        for opportunity, source in opportunity_query.all():
            searchable = f"{opportunity.title or ''} {opportunity.description or ''} {opportunity.sector or ''}".lower()
            score = sum(term in searchable for term in terms) / len(terms) if terms else 0.0
            if not terms or score > 0:
                results.append((opportunity, source, score))

        results.sort(key=lambda item: item[2], reverse=True)
        return results
    finally:
        session.close()


def delete_opportunity(opportunity_id):
    """Delete an opportunity and its stored similarity results."""
    session: Session = SessionLocal()
    try:
        opportunity = session.get(Opportunity, opportunity_id)
        if opportunity is None:
            return False

        session.query(SimilarityResult).filter(
            SimilarityResult.opportunity_id == opportunity_id
        ).delete(synchronize_session=False)
        session.delete(opportunity)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
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
