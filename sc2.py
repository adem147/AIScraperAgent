import json

import pandas as pd
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError
from requests import session

from database.models import Opportunity, BestApiEndpoint,Source
from database.models import Opportunity
from database.storage import get_best_api_for_source, save_best_api_for_source
from scraper.json_parser import create_sample_text, get_middle_response_items, parse_json_response
from scraper.embedding import score_response_usefulness
from scraper.filtering import (
    clean_api_dataframe,
    fetch_best_api_data,
    filter_relevant,
    normalize_world_bank,
    process_payload
)


#url = "https://projects.worldbank.org/en/projects-operations/opportunities"
ENDPOINT_RESULTS = []
# schema_registry.py

SCHEMA_REGISTRY = {
    "worldbank": {
        "data_path": ["data", "items"],
    },
    "tuneps": {
        "data_path": ["payload", "data"],  
    }
}

def handle_response(response):
    if response.request.resource_type in ["fetch", "xhr"]:
        # print(f"\n {response.request.method} {response.url}")

        parsed_data = parse_json_response(response)


        if parsed_data is not None:
            sample_items = get_middle_response_items(parsed_data, limit=5)
           # print(f"Sample items for embedding: {sample_items}")  # Print the sample items for debugging
            sample_text = create_sample_text(sample_items)
            print("Sample text for embedding:", sample_text,"source:",response.url)  # Print the first 200 characters of the sample text for debugging
            usefulness = score_response_usefulness(sample_text)

            if usefulness:
                ENDPOINT_RESULTS.append({
                    "method": response.request.method,
                    "url": response.url,
                    "similarity_score": usefulness["similarity_score"],
                    "sample_items": sample_items,
                })
               # print("Embedding similarity score:", usefulness["similarity_score"])
        else:
            pass
           # print("Content-Type:", response.headers.get("content-type"))

def get_filtered_df(source : Source):

    url = source.url
    source_id = source.id


    """Run the scraper flow and return the filtered DataFrame."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        existing_endpoint = get_best_api_for_source(source_id)

        best_api = None

        if existing_endpoint:
            print("Best API already exists, skipping discovery")
            best_api = existing_endpoint
        else:
            print("Searching for best API...")

            try:
                page = browser.new_page()
                page.on("response", handle_response)
                page.goto(url, wait_until="networkidle",timeout=50000)  # Wait until network is idle or timeout after 50 seconds
            except TimeoutError as e:
                print(f"Timeout error occurred while waiting for API responses: {e}")
            except Exception as e:
                print(f"Unexpected error occurred while waiting for API responses: {e}")

            ranked_results = sorted(
                ENDPOINT_RESULTS,
                key=lambda item: item["similarity_score"],
                reverse=True
            )

            best_api = ranked_results[0]

            best_api = BestApiEndpoint(
                source_id=source_id,
                endpoint_url=best_api["url"],
                method=best_api["method"],
                similarity_score=best_api["similarity_score"],
            )

            save_best_api_for_source(best_api)
                
        filtered_df = pd.DataFrame()

      
        full_payload = fetch_best_api_data(best_api.endpoint_url)
       
        processed_payload = process_payload(full_payload.copy(), SCHEMA_REGISTRY.get(source.organization_name.lower(), {}).get("data_path", []))
       

        if processed_payload is not None:

            cleaned_df = clean_api_dataframe(processed_payload)
            normalized_df = normalize_world_bank(cleaned_df)
            filtered_df = filter_relevant(normalized_df)



            print("\n===== CLEANED DATAFRAME SAMPLE CREATED =====")
            with open("output.txt", "w", encoding="utf-8") as handle:
                handle.write(filtered_df.head(25).to_string())

        browser.close()
        return filtered_df


if __name__ == "__main__":
    result = get_filtered_df()


