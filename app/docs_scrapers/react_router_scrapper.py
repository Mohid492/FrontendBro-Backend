from selenium import webdriver
import time
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()
url="https://reactrouter.com/"

def React_router_doc_scrapper():
    browser = webdriver.Edge()
    browser.maximize_window()
    browser.get(url)
    browser.find_element(By.XPATH,"//a[normalize-space()='Docs']").click()
    time.sleep(2)  # Wait for the page to load
    side_bar=browser.find_element(By.CSS_SELECTOR,"div[class='sticky bottom-0 top-16 hidden w-[--nav-width] flex-col gap-3 self-start overflow-auto py-6 pl-8 pr-6 lg:flex h-[calc(100vh-var(--header-height))]']")
    nav_links=side_bar.find_elements(By.TAG_NAME,"a")
    hrefs= [link.get_attribute('href') for link in nav_links]
    del hrefs[:2]
    del hrefs[23:26]
    del hrefs[-3:]
    del hrefs[148]
    logger.info(f"Total links in the nav bar of React Router: {len(hrefs)}")
    extracted_data=[]
    for href in hrefs:
        try:
            logger.info(f"Extracting data from {href}")
            browser.get(href)
            time.sleep(2)
            # This sends a request to the web page at
            # the URL stored in href and gets the page’s content.
            response=requests.get(href)
            #This takes the text (HTML) from the
            # web page response and saves it in html_content
            html_content=response.text
            #This uses BeautifulSoup to turn the HTML content into a format that’s
            # easy to search and work with in Python.
            soup=BeautifulSoup(html_content,features="html.parser")
            # removing links
            for a in soup.find_all("a"):
                a.decompose()
            page_text=soup.get_text().strip('\n')
            extracted_data.append(page_text+ "\n\n")
            time.sleep(1)
            logger.info("Data extraction done")
        except:
            logger.error("Data extraction failed")

    with open("app/docs_scrapers/extracted_data/Extracted_React-Router_doc.txt","w",encoding="utf-8") as f:
        f.writelines(extracted_data)

    browser.quit()
