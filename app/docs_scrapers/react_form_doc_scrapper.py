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

def React_hook_form_doc_scrapper():

    options = Options()
    options.add_argument("--headless")  # Run Edge in headless mode
    browser = webdriver.Edge(options=options)
    browser.implicitly_wait(2)
    browser.get("https://react-hook-form.com/")
    logger.info("Extracting React hook form documentation")
    browser.find_element(By.XPATH,"//span[normalize-space()='Get Started']").click()
    logger.info("Navigated to the documentation section")
    time.sleep(2)

    side_navbar=browser.find_element(By.CLASS_NAME,"SideMenu_menu__MO_F2")
    logger.info("Side navbar found")
    links=side_navbar.find_elements(By.TAG_NAME,"a")
    urls=[link.get_attribute('href') for link in links]
    del urls[-3:]
    urls.pop(2)

    browser.find_element(By.CSS_SELECTOR,"body > div:nth-child(1) > div:nth-child(5) > nav:nth-child(1) > a:nth-child(3)").click()
    browser.find_element(By.XPATH,"//a[@aria-label='read more about useForm']").click()
    side_navbar=browser.find_element(By.CSS_SELECTOR,"body > div:nth-child(1) > div:nth-child(6) > div:nth-child(3) > aside:nth-child(1) > div:nth-child(1)")
    new_links=side_navbar.find_elements(By.TAG_NAME,"a")
    new_urls=[link.get_attribute('href') for link in new_links]
    # adding these urls
    urls.extend(new_urls)

    browser.find_element(By.CSS_SELECTOR,"body > div:nth-child(1) > div:nth-child(5) > nav:nth-child(1) > a:nth-child(5)").click()
    side_navbar=browser.find_element(By.CSS_SELECTOR,".SideMenu_menu__MO_F2")
    another_new_links=side_navbar.find_elements(By.TAG_NAME,"a")
    another_new_urls=[link.get_attribute('href') for link in another_new_links]
    # adding these urls
    urls.extend(another_new_urls)

    # Now scraping Data after extracting all urls
    logger.info("Extracting React Hook Form documentation")
    extracted_data=[]
    for url in urls:
        try:
            logger.info(f"Extracting data from {url}")
            browser.get(url)
            time.sleep(1)
            response=requests.get(url)
            html_content=response.text
            soup=BeautifulSoup(html_content,features="html.parser")
            # removing links
            for a in soup.find_all("a"):
                a.decompose()
            # removing buttons
            for button in soup.find_all("button"):
                button.decompose()
            page_text=soup.get_text().strip('\n')
            extracted_data.append(page_text+ "\n\n")
            time.sleep(1)
            logger.info("Data extraction done")
        except:
            logger.error("Data extraction failed")


    with open("app/docs_scrapers/extracted_data/Extracted_React-hook-form_doc.txt","w",encoding="utf-8") as f:
        f.writelines(extracted_data)

    browser.quit()