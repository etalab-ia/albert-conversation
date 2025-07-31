import requests
import re
from bs4 import BeautifulSoup as bs

def convert_to_markdown(article):
    # Extract the HTML content and convert to markdown
    # Initialize markdown text
    markdown_text = ""

    # Process headings
    for heading in article.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(heading.name[1])
        markdown_text += '#' * level + ' ' + heading.get_text(strip=True) + '\n\n'

    # Process paragraphs
    for para in article.find_all('p'):
        markdown_text += para.get_text(strip=True) + '\n\n'

    # Process lists
    for ul in article.find_all('ul'):
        for li in ul.find_all('li'):
            markdown_text += '* ' + li.get_text(strip=True) + '\n'
        markdown_text += '\n'

    for ol in article.find_all('ol'):
        for i, li in enumerate(ol.find_all('li')):
            markdown_text += f"{i+1}. " + li.get_text(strip=True) + '\n'
        markdown_text += '\n'

    # Process links
    for link in article.find_all('a'):
        href = link.get('href', '')
        text = link.get_text(strip=True)
        if href and text:
            markdown_text += f"[{text}]({href})\n\n"

    # Clean up extra newlines and spaces
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
    text = markdown_text.strip()
    
    return text



def annuaire_check(what, where):
    url = "https://lannuaire.service-public.fr/recherche?whoWhat={what}&where={where}"

    response = requests.get(url.format(what=what, where=where))
    chunks = []

    try:
        # Extract results
        soup = bs(response.text)

        # find id=result-search
        soup = soup.find(id="result-search")

        # extract all "class="fr-link" data-test="searchResult-link"" with href 
        links = soup.find_all("a", class_="fr-link", attrs={"data-test": "searchResult-link"})

        #print(links)
        links_dict = {link.text: link.get("href") for link in links[:4]}

        for link in list(links_dict.values()):
            soup = requests.get(link)
            soup = bs(soup.text)
            #find div "article" (<article>)

            article = soup.find("article")

            #print(article.prettify())
            text = convert_to_markdown(article)
            chunks.append(text)
    except Exception as e:
        print("Aucun résultat trouvé pour {what} {where}")

    #[print(chunk) for chunk in chunks]

    if chunks:
        return chunks
    else:
        return f"Aucune information trouvée pour {what} {where}, cette personne ou ce lieu n'existe pas ou n'est pas inscrit dans l'annuaire. Informez l'utilisateur si besoin."
