import pandas as pd
import requests


def fetch_best_api_data(best_result):
    """Fetch the full payload from the top-ranked API endpoint."""
    if not best_result:
        return None

    request_url = best_result.get("url")
    if not request_url:
        return None

    response = requests.get(request_url, timeout=30)
    response.raise_for_status()
    return response.json()


def clean_api_dataframe(data):
    """Convert API JSON into a simple pandas DataFrame and clean it."""
    if data is None:
        return pd.DataFrame()

    return pd.json_normalize(data)


def normalize_world_bank(df):
    """Rename the World Bank columns to a simple, reusable schema."""
    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return pd.DataFrame()

    if df.empty:
        return df.copy()

    rename_map = {
        "notice_type": "type",
        "noticedate": "date",
        "notice_lang_name": "language",
        "notice_status": "status",
        "submission_deadline_date": "submission_deadline",
        "project_ctry_name": "country",
        "project_id": "id",
        "project_name": "title",
        "bid_description": "description",
        "procurement_group_desc": "group",
        "submission_date": "submission_date",
        "market_approach_name": "market_approach",
        "market_approach_region_name": "market_region",
        "procurement_major_sector_name": "sector",
    }

    normalized_df = df.copy()
    normalized_df = normalized_df.rename(columns=rename_map)

    return normalized_df


def filter_relevant(df):
    """Keep rows that still look relevant after normalization."""

    FINAL_COLUMNS = [
    "id",
    "title",
    "description",
    "organization",
    "submission_deadline",
    "country",
    "sector",
    "url"
    ]

    if df is None:
        return pd.DataFrame()

    if not isinstance(df, pd.DataFrame):
        try:
            df = pd.DataFrame(df)
        except Exception:
            return pd.DataFrame()

    if df.empty:
        return df.copy()

    df = df[[col for col in FINAL_COLUMNS if col in df.columns]]

    return df.copy()
