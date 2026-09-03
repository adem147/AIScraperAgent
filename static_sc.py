import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit

from scraper.html_extractor import extract_from_link
from LLM.nlp_extractor import extract_from_text


NUMBER_OF_EXTRACTED_LINKS = 20

def get_stripped_url(url):
    """Return the URL directory without query parameters or fragments."""
    parsed_url = urlsplit(url.strip())
    directory = parsed_url.path.rsplit("/", 1)[0] + "/"
    return urlunsplit((parsed_url.scheme, parsed_url.netloc, directory, "", ""))


def scrape_static_site(base_url):
    all_items = []
    links = []

    page_num = 0

    while True:

        url = (
            f"{base_url}"
            f"?pageNum_rsAllAo={page_num}"
            f"&totalRows_rsAllAo=255"
            f"&allao"
        )

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for div in soup.find_all("div", class_="appeloffre"):
            a = div.find("a", class_="lienappel")

            if a:
                links.append(a.get("href"))
            else: 
                break

        # Extract opportunities
       # items = extract_opportunities(soup, base_url)

        #print(soup)

        #all_items.extend(items)

        page_num += 1

        if page_num == 1:
            break

    return links


def get_filtred_df_static(source):

    base_url = source.url
    
    striped_url = get_stripped_url(base_url)

    filtred_data = [] 

    links = scrape_static_site(base_url)

    print(f"Getting only the first : "+ str(NUMBER_OF_EXTRACTED_LINKS) + " links from website" + {source.title})
    links = links[:NUMBER_OF_EXTRACTED_LINKS]
    for link in links:
        text = extract_from_link(urljoin(striped_url, link))
        opp = extract_from_text(text)
        if(opp.get("title") is None or opp.get("description") is None):
            continue
        filtred_data.append(opp)
    return pd.DataFrame(filtred_data)
        
    





