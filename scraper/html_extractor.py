import requests
from bs4 import BeautifulSoup

def extract_ao_text(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    container = soup.find("div", class_="actus1")

    if not container:
        return None

    # remove unwanted tags inside it
    for tag in container(["script", "style", "button"]):
        tag.decompose()

    text = container.get_text(separator=" ", strip=True)

    return text
