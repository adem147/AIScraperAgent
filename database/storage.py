from datetime import datetime, time

import pandas as pd
from sqlalchemy.orm import Session
from database.db import Base, SessionLocal, engine
from database.models import BestApiEndpoint, Opportunity, SimilarityResult, Source
from scraper.hashing import generate_hash


def initialize_database():
    """Create database tables when they do not exist yet."""
    Base.metadata.create_all(engine)


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


def insert_opportunities(source, dataframe):
    """Insert one scraper's filtered DataFrame as a separate batch."""
    session: Session = SessionLocal()
    opportunities = []
    try:
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
                session.refresh(opportunity)
                opportunities.append(opportunity)
            except Exception:
                session.rollback()
        return opportunities
    finally:
        session.close()


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


def get_opportunities_by_ids(opportunity_ids):
    """Retrieve opportunities and sources for the requested IDs."""
    if not opportunity_ids:
        return []
    session: Session = SessionLocal()
    try:
        return (
            session.query(Opportunity, Source)
            .join(Source, Opportunity.source_id == Source.id)
            .filter(Opportunity.id.in_(opportunity_ids))
            .all()
        )
    finally:
        session.close()


def save_opportunity(opportunity):
    """Persist an already-created opportunity and return its ID."""
    session: Session = SessionLocal()
    try:
        session.add(opportunity)
        session.commit()
        session.refresh(opportunity)
        return opportunity.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_procurement_notice(notice):
    """Persist a processed notice using the current opportunity schema."""
    submission_deadline = parse_datetime(notice.dates.submission_deadline)
    published_date = parse_datetime(notice.dates.publication_date)
    opportunity = Opportunity(
        hash_id=generate_hash(
            notice.objet,
            submission_deadline.isoformat() if submission_deadline else "",
            notice.synthese_opportunite or notice.objet,
        ),
        title=notice.objet,
        description=notice.synthese_opportunite or notice.objet,
        url=notice.source_url or "",
        published_date=published_date,
        submission_deadline=submission_deadline,
        sector=notice.sector,
    )
    return save_opportunity(opportunity)


def search_opportunities(query="", source_id=None, deadline_after=None):
    """Find opportunities matching text, source, and an inclusive deadline date."""
    session: Session = SessionLocal()
    try:
        opportunity_query = session.query(Opportunity, Source).outerjoin(
            Source, Opportunity.source_id == Source.id
        )
        if source_id is not None:
            opportunity_query = opportunity_query.filter(Opportunity.source_id == source_id)
        if deadline_after is not None:
            deadline_limit = datetime.combine(deadline_after, time.min)
            opportunity_query = opportunity_query.filter(
                Opportunity.submission_deadline >= deadline_limit
            )

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
