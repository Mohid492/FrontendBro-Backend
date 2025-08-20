from fastapi import status,APIRouter
# scraping functions
from ..docs_scrapers.react_doc_scrapper import React_docs_scrapper
from ..docs_scrapers.tailwindcss_doc_scrapper import Tailwindcss_docs_scrapper
from ..docs_scrapers.tailwindcss_ui_kit_doc_scrapper import Tailwindcss_ui_kit_docs_scrapper
from ..docs_scrapers.react_form_doc_scrapper import React_hook_form_doc_scrapper
from ..docs_scrapers.axios_scrapper import Axios_doc_scrapper
from ..docs_scrapers.react_router_scrapper import React_router_doc_scrapper
from ..docs_scrapers.tailwindcss_templates_doc_scrapper import Tailwindcss_templates_docs_scrapper
router = APIRouter(
    prefix='/scrape',
    tags=['scraper']
)

@router.post("/scrape-react-docs", status_code=status.HTTP_200_OK)
async def scrape_react_docs():
    React_docs_scrapper()
    return {"message": "React documentation scraping completed successfully."}

@router.post("/scrape-tailwindcss-docs", status_code=status.HTTP_200_OK)
async def scrape_tailwindcss_docs():
    Tailwindcss_docs_scrapper()
    return {"message": "Tailwind CSS documentation scraping completed successfully."}

@router.post("/scrape-tailwindcss-templates-docs", status_code=status.HTTP_200_OK)
async def scrape_tailwindcss_templates_docs():
    Tailwindcss_templates_docs_scrapper()
    return {"message": "Tailwind CSS templates documentation scraping completed successfully."}

@router.post("/scrape-tailwindcss-ui-kit-docs", status_code=status.HTTP_200_OK)
async def scrape_tailwindcss_ui_kit_docs():
    Tailwindcss_ui_kit_docs_scrapper()
    return {"message": "Tailwind CSS UI Kit documentation scraping completed successfully."}

@router.post("/scrape-react-hook-form-docs", status_code=status.HTTP_200_OK)
async def scrape_react_hook_form_docs():
    React_hook_form_doc_scrapper()
    return {"message": "React Hook Form documentation scraping completed successfully."}

@router.post("/scrape-axios-docs", status_code=status.HTTP_200_OK)
async def scrape_axios_docs():
    Axios_doc_scrapper()
    return {"message": "Axios documentation scraping completed successfully."}

@router.post("/scrape-react-router-docs", status_code=status.HTTP_200_OK)
async def scrape_react_router_docs():
    React_router_doc_scrapper()
    return {"message": "React Router documentation scraping completed successfully."}
@router.post("/scrape-all-docs", status_code=status.HTTP_200_OK)
async def scrape_all_docs():
    React_docs_scrapper()
    Tailwindcss_docs_scrapper()
    Tailwindcss_templates_docs_scrapper()
    Tailwindcss_ui_kit_docs_scrapper()
    React_hook_form_doc_scrapper()
    Axios_doc_scrapper()
    React_router_doc_scrapper()
    return {"message": "All documentation scraping completed successfully."}
