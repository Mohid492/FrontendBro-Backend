from selenium import webdriver
import time
from selenium.webdriver.common.by import By
import logging
from selenium.webdriver.support.ui import Select
# Configure logging
logging.basicConfig(level=logging.INFO)

# Get the root logger
logger = logging.getLogger()
# Set up Edge options for headless mode

def Tailwindcss_templates_docs_scrapper():
    browser = webdriver.Edge()
    browser.implicitly_wait(8)
    browser.maximize_window()
    url = "https://tailwindcss.com/"
    browser.get(url)
    logger.info("Tailwind css templates documentation scraper started.")
    browser.find_element(By.XPATH, "//a[normalize-space()='Docs']").click()
    browser.find_element(By.XPATH, "//a[normalize-space()='Components']").click()

    section = browser.find_element(By.CSS_SELECTOR, "#product-marketing-sections")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    urls = []
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-marketing-elements")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR,
                                   "section[id='product-marketing-feedback'] ul[class='grid grid-cols-1 gap-10 sm:grid-cols-2 sm:max-md:gap-x-5 lg:grid-cols-3 xl:grid-cols-4']")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-marketing-page-examples")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-application-shells")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-headings")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-data-display")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-lists")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-forms")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-navigation")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-overlays")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-elements")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-application-ui-layout")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    section = browser.find_element(By.CSS_SELECTOR, "#product-ecommerce-components")
    a_tag = section.find_elements(By.TAG_NAME, 'a')
    for a in a_tag:
        href = a.get_attribute('href')
        if href:
            urls.append(href)

    logger.info(f"Total URLs collected: {len(urls)}")
    # After getting all the required links we are now going to scrape data from each page

    count = 1
    for url in urls:
        logger.info(f"Processing URL {count}: {url}")
        browser.get(url)
        element_found = False
        # button finding
        btns = browser.find_elements(By.TAG_NAME, "button")
        for btn in btns:

            if btn.text == 'Code':
                btn.click()
                element_found = True

        if not element_found:
            continue

        time.sleep(2)

        selects = browser.find_elements(By.TAG_NAME, 'select')
        visible_select = None
        for s in selects:
            if s.is_displayed():
                visible_select = s
                break

        if visible_select:
            select = Select(visible_select)
            options = select.options

            select.select_by_value('react')
            time.sleep(15)

        else:
            logger.warning("No visible <select> element found on this page.")

        # printing out the text
        h1 = browser.find_element(By.TAG_NAME, "h1")
        paras = browser.find_elements(By.TAG_NAME, "p")
        paragraph = " ".join(paras[5].text.split())
        text_box = browser.find_elements(By.TAG_NAME, "pre")
        logger.info(f"{h1.text} :")
        logger.info(paragraph)
        logger.info("code:")
        logger.info(text_box[0].text)
        count += 1

        # Writting data to file
        with open("app/docs_scrapers/extracted_data/Extracted_Tailwindcss-Templates_doc.txt", "a", encoding="utf-8") as f:
            f.write(h1.text + ":" + "\n")
            f.write(paragraph + "\n")
            f.write("code:\n")
            f.write(text_box[0].text + "\n")
    browser.quit()

