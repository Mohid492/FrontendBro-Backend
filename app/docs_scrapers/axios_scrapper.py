from selenium import webdriver
import requests
from bs4 import BeautifulSoup
import logging
from selenium.webdriver.edge.options import Options
# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()

def Axios_doc_scrapper():

    options = Options()
    options.add_argument("--headless")  # Run Edge in headless mode
    browser = webdriver.Edge(options=options)
    browser.implicitly_wait(2)

    logger.info("Extracting Axios")
    url="https://www.freecodecamp.org/news/how-to-use-axios-with-react/#heading-how-to-make-a-get-request"
    browser.get(url)
    response=requests.get(url)
    html_content=response.text
    soup=BeautifulSoup(html_content,features="html.parser")
    # removing links
    for a in soup.find_all("a"):
        a.decompose()
    page_text=soup.get_text().strip('\n')
    # Define markers for start and end
    start_marker = "Make a GET Request"
    end_marker = "What's Next?"
    # Find the start of the desired text
    start_index = page_text.find(start_marker)
    # Find the end marker beginning from start_index
    end_index = page_text.find(end_marker, start_index)
    filtered_text = page_text[start_index:end_index]

    with open("app/docs_scrapers/extracted_data/Extracted_Axios.txt","w",encoding="utf-8") as f:
        f.writelines(filtered_text)
    logger.info("Data extraction completed and saved to Extracted_Axios.txt")
    browser.quit()