from selenium import webdriver
import time
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()

def Tailwindcss_ui_kit_docs_scrapper():

    options = Options()
    options.add_argument("--headless")  # Run Edge in headless mode
    browser = webdriver.Edge(options=options)
    browser.get("https://catalyst.tailwindui.com/docs")

    nav_bar=browser.find_element(By.CSS_SELECTOR,"nav[class='sticky top-16 hidden max-h-[calc(100dvh-(--spacing(16)))] w-48 shrink-0 overflow-y-auto pt-12 pb-16 lg:block']")
    nav_links=nav_bar.find_elements(By.TAG_NAME,'a')
    hrefs= [link.get_attribute('href') for link in nav_links]

    logger.info("Extracting Tailwind Templates documentation")
    extracted_data=[]
    for href in hrefs:
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
            extracted_data.append(page_text+ "\n\n")
            time.sleep(1)
            logger.info("Tailwindcss Templates data extraction done")
        except:
            logger.error("Tailwindcss Templates data extraction failed")

    with open("app/docs_scrapers/extracted_data/Extracted_Tailwind-UI-Kit_doc.txt","w",encoding="utf-8") as f:
        f.writelines(extracted_data)

    browser.quit()