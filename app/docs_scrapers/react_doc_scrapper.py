from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
import requests
from bs4 import BeautifulSoup
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()


url="https://react.dev/reference/react/hooks"

def React_docs_scrapper():
    logger.info("Extracting React documentation")
    options = Options()
    options.add_argument("--headless")  # Run Edge in headless mode
    browser = webdriver.Edge(options=options)
    browser.implicitly_wait(2)
    url = "https://react.dev/reference/react/hooks"
    browser.get(url)
    navbar=browser.find_element(By.CSS_SELECTOR,"nav[class='w-full pt-6 scrolling-touch lg:h-auto grow pe-0 lg:pe-5 lg:pb-16 md:pt-4 lg:pt-4 scrolling-gpu']")
    links=navbar.find_elements(By.TAG_NAME,'a')
    urls=[link.get_attribute('href') for link in links]
    logger.info("Extracting React documentation")
    unwanted_patterns = [
            r"Copyright © Meta Platforms, Inc.*",
            r"no uwu plzuwu\?Logo byMoreOn this page.*"
        ]

    extracted_data=[]

    for href in urls:
        try:
            logger.info(f"Extracting data from {href}")
            browser.get(href)
            time.sleep(2)
            response=requests.get(href)
            html_content=response.text
            soup=BeautifulSoup(html_content,features="html.parser")
            # removing links
            for a in soup.find_all("a"):
                a.decompose()

            page_text=soup.get_text().strip('\n')
            # removing unwanted patterns
            for extracted_text in unwanted_patterns:
                page_text = re.sub(extracted_text, "", page_text)

            # storing extracted text in a file
            extracted_data.append(page_text + "\n\n")
            time.sleep(1)
            logger.info("React data extraction done")
        except:
            logger.error("React data extraction failed")

    with open("app/docs_scrapers/extracted_data/Extracted_React_doc.txt","w",encoding="utf-8") as f:
        f.writelines(extracted_data)

    browser.quit()