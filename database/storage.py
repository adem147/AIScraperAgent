from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.db import SessionLocal
from database.models import BestApiEndpoint, SimilarityResult, Source, Opportunity


def get_all_sources():
    """Retrieve all sources from the database."""
    session: Session = SessionLocal()
    try:
        return session.query(Source).all()
    finally:
        session.close()


def seed_default_sources():
    """Ensure default sources exist in the database."""
    session: Session = SessionLocal()
    try:
        if session.query(Source).count() == 0:
            sources = [
                Source(
                    id=1,
                    title="World Bank Opportunities",
                    url="https://projects.worldbank.org/en/projects-operations/opportunities",
                    scrape_type="dynamic",
                ),
                Source(
                    id=2,
                    title="INTT Appels d'offres",
                    url="https://www.intt.tn/fr/index.php",
                    scrape_type="static",
                ),
            ]
            session.add_all(sources)
            session.commit()
            print("Default sources seeded successfully.")
    except Exception as e:
        session.rollback()
        print("Error seeding sources:", e)
    finally:
        session.close()


def get_best_api_for_source(source_id_or_url):
    """Retrieve the best API endpoint for a given source ID or source URL."""
    session: Session = SessionLocal()
    try:
        res = (
            session.query(BestApiEndpoint)
            .filter(
                (BestApiEndpoint.source_url == str(source_id_or_url)) |
                (BestApiEndpoint.id == (source_id_or_url if isinstance(source_id_or_url, int) else -1))
            )
            .first()
        )
        return res
    except Exception as e:
        session.rollback()
        print("get_best_api_for_source info:", e)
        return None
    finally:
        session.close()


def save_best_api_for_source(best_api_endpoint: BestApiEndpoint):
    """Persist the best API endpoint for a website, only once per source ID."""
    session: Session = SessionLocal()
    try:
        session.add(best_api_endpoint)
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
        # Clear previous run results to keep only the fresh top results
        session.query(SimilarityResult).delete()
        session.add_all(results)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print("Error saving similarity results:", e)
        return False
    finally:
        session.close()


def get_top_5_results() -> List[Dict[str, Any]]:
    """Fetch the top 5 results saved in the database."""
    session: Session = SessionLocal()
    try:
        # First attempt: Read from similarity_results table
        sim_results = (
            session.query(SimilarityResult)
            .order_by(SimilarityResult.similarity_score.desc())
            .limit(5)
            .all()
        )

        formatted_results = []

        if sim_results:
            for item in sim_results:
                opp = session.query(Opportunity).filter(Opportunity.id == item.opportunity_id).first()
                formatted_results.append({
                    "id": item.id,
                    "opportunity_id": item.opportunity_id,
                    "title": item.title or (opp.title if opp else "Opportunity"),
                    "similarity_score": round(float(item.similarity_score), 3),
                    "similarity_score_pct": f"{round(float(item.similarity_score) * 100, 1)}%",
                    "description": opp.description if opp else "",
                    "organization": opp.organization if opp and opp.organization else "Procurement Authority",
                    "country": opp.country if opp and opp.country else "Global",
                    "sector": opp.sector if opp and opp.sector else "Information Technology",
                    "submission_deadline": opp.submission_deadline if opp and opp.submission_deadline else "N/A",
                    "budget": opp.budget if opp and opp.budget else "N/A",
                    "document_url": (opp.document_url or opp.url) if opp else "#",
                })
            return formatted_results

        # Fallback: Read directly from opportunities table if similarity_results is empty
        opps = (
            session.query(Opportunity)
            .order_by(
                Opportunity.relevance_score.desc().nullslast(),
                Opportunity.id.desc()
            )
            .limit(5)
            .all()
        )

        for opp in opps:
            score = opp.relevance_score if opp.relevance_score is not None else 0.85
            formatted_results.append({
                "id": opp.id,
                "opportunity_id": opp.id,
                "title": opp.title,
                "similarity_score": round(float(score), 3),
                "similarity_score_pct": f"{round(float(score) * 100, 1)}%",
                "description": opp.description or opp.synthese_opportunite or "",
                "organization": opp.organization or "Procurement Authority",
                "country": opp.country or "Global",
                "sector": opp.sector or "Information Technology",
                "submission_deadline": opp.submission_deadline or "N/A",
                "budget": opp.budget or "N/A",
                "document_url": opp.document_url or opp.url or "#",
            })

        return formatted_results

    except Exception as e:
        print("Error fetching top 5 results:", e)
        return []
    finally:
        session.close()


def get_db_stats() -> Dict[str, Any]:
    """Retrieve summary counts and stats from the database."""
    session: Session = SessionLocal()
    try:
        opp_count = session.query(Opportunity).count()
        sim_count = session.query(SimilarityResult).count()
        top_sim = (
            session.query(SimilarityResult)
            .order_by(SimilarityResult.similarity_score.desc())
            .first()
        )
        top_score = round(float(top_sim.similarity_score), 3) if top_sim else 0.0

        return {
            "total_opportunities": opp_count,
            "similarity_results_count": sim_count,
            "top_similarity_score": top_score,
            "top_similarity_pct": f"{round(top_score * 100, 1)}%" if top_score > 0 else "0%",
        }
    except Exception as e:
        print("Error fetching DB stats:", e)
        return {
            "total_opportunities": 0,
            "similarity_results_count": 0,
            "top_similarity_score": 0.0,
            "top_similarity_pct": "0%",
        }
    finally:
        session.close()
        
