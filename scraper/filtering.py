import pandas as pd
import requests


def fetch_best_api_data(best_api_url):
    """Fetch the full payload from the top-ranked API endpoint."""
    if not best_api_url:
        return None

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://www.tuneps.tn",
        "Referer": "https://www.tuneps.tn/portail/offres"
    }

    payload = {
        "listSort": [],
        "dataSearch": [
            {
                "key": "publicYn",
                "value": "Y",
                "specificSearch": "="
            }
        ],
        "listCol": [],
        "pagination": {
            "offSet": 0,
            "limit": 5
        },
        "sort": {
            "nameCol": "publicDt",
            "direction": "desc nulls last"
        }
    }

    response = requests.post(
    best_api_url,
    headers=headers,
    json=payload,
    verify=False
    )
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


def process_payload(full_payload,path):
    """Extract the relevant data block from the full payload based on the schema path."""
    if path is None or not isinstance(path, list):
        return None

    for key in path:
        if isinstance(full_payload, dict):
            full_payload = full_payload.get(key)
        else:
            return None

    return full_payload


def filter_relevant(df):
    """Keep rows that still look relevant after normalization."""

    FINAL_COLUMNS = [
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
