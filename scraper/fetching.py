import requests
from urllib.parse import urlsplit, urlunsplit
from data.worldbank import method, payload



def fetch_best_api_data(best_api_url, request_method=method):
    """Fetch the full payload from the top-ranked API endpoint."""
    if not best_api_url:
        return None

    parsed_url = urlsplit(best_api_url.strip())
    best_api_url = urlunsplit(
        (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "")
    )
    print("striped url : " ,best_api_url)

    request_kwargs = {"verify": False, "timeout": 30}
    if request_method.upper() == "GET":
        request_kwargs["params"] = payload
    else:
        request_kwargs["json"] = payload

    try:
        response = requests.post(best_api_url, params=payload, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        print(f"Request failed: {error}")
    except ValueError as error:
        print(f"Invalid JSON response: {error}")

    return None