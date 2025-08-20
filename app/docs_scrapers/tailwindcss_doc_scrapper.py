from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()
def Tailwindcss_docs_scrapper():
    url = "https://tailwindcss.com/"
    options = Options()
    options.add_argument("--headless")  # Run Edge in headless mode
    browser = webdriver.Edge(options=options)
    browser.implicitly_wait(2)
    browser.get(url)
    logger.info("Extracting Tailwind documentation")
    browser.find_element(By.XPATH,"//a[normalize-space()='Docs']").click()
    logger.info("Docs link found and clicked")
    time.sleep(2)
    nav_bar=browser.find_element(By.CSS_SELECTOR,"div[class='sticky top-14.25 bottom-0 left-0 h-full max-h-[calc(100dvh-(var(--spacing)*14.25))] w-2xs overflow-y-auto p-6']")
    logger.info("Nav bar found")
    nav_links = nav_bar.find_elements(By.TAG_NAME,'a')
    hrefs= [link.get_attribute('href') for link in nav_links]
    del hrefs[1:10]
    logger.info("Extracting Tailwind documentation")
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
            logger.info("Tailwind data extraction done")
        except:
            logger.error("Tailwind data extraction failed")

    with open("app/docs_scrapers/extracted_data/Extracted_Tailwind_doc.txt","w",encoding="utf-8") as f:
        f.writelines(extracted_data)

    browser.quit()
