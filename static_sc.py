import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scraper.html_extractor import extract_from_link
from LLM.nlp_extractor import extract_from_text


base_url = "https://www.intt.tn/fr/index.php"
striped_url = "https://www.intt.tn/fr/"


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


def get_filtred_data():

    filtred_data = [] 

    print("======= processing source : INTT ======")

    links = scrape_static_site(base_url)
    links = links[:10]
    for link in links:
        text = extract_from_link(striped_url,link)
        opp = extract_from_text(text)
        if(opp["title"] is None or opp["description"] is None):
            continue
        filtred_data.append(opp)
    return filtred_data
        
    


if __name__ == "__main__":
   pass




