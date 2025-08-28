from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.config import settings
from app.routers import scraper,agent,generate_vector
from app.routers.auth.auth import router as auth_router
import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    # Your existing origins
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    # Add both ports to be safe
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI application!"}


app.include_router(auth_router)
app.include_router(scraper.router)
app.include_router(generate_vector.router)
app.include_router(agent.router)


