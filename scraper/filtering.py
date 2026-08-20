import pandas as pd
import requests
import json
from typing import Any, Dict, List, Optional



def fetch_best_api_data(best_api):
    """Fetch the full payload from the top-ranked API endpoint."""
    if not best_api:
        return None


    url = best_api.url

    headers = best_api.header

    payload = best_api.payload

    response = requests.post(
    url=url,
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


def normalize_world_bank(df,mapper:dict):
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

    if mapper is None or not isinstance(mapper, dict):
        print("Mapper is None or not a dictionary. Returning original DataFrame.")
        return df.copy()

    rename_map = mapper  # Use the provided mapping for renaming

    normalized_df = df.copy()
    normalized_df = normalized_df.rename(columns=rename_map)

    return normalized_df

def process_payload(full_payload: Any, path: List[str]) -> List[Any]:
    """Extract relevant data block from nested payload using a schema path."""

    if not full_payload or not path:
        return []

    # Navigate through nested dict
    for key in path:
        if isinstance(full_payload, dict):
            full_payload = full_payload.get(key)
        else:
            return []

    # Normalize output to list safely
    if full_payload is None:
        return []

    if isinstance(full_payload, list):
        return full_payload

    # wrap single object into list
    return [full_payload]


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
