# 🚀 Frontend Bro

**Frontend Bro** is a FastAPI-powered RAG application that combines **web scraping, vector search, and AI-powered code generation** to create fully functional frontend pages in **React + Tailwind CSS**.  

The project integrates **OpenAI, LangChain, ChromaDB, Redis, PostgreSQL, and OAuth2 authentication** to provide a seamless developer experience.  

---

## 🔥 Features

- **Scraping API** – Built with **FastAPI**, **Selenium**, and **BeautifulSoup** to scrape data from React and Tailwind CSS docs.  
- **Vector Storage** – Uses **ChromaDB** to store scraped docs as embeddings.  
- **RAG Pipeline** – Powered by **LangChain + OpenAI** to generate **fully working React + Tailwind CSS code**.  
- **Chat Storage** – Stores chat history in **Redis** and **PostgreSQL**, with summarized context for efficiency.  
- **Authentication** – Secured with **OAuth2** authentication.  
- **Database Migrations** – Managed via **Alembic** for PostgreSQL schema updates.  

---

## ⚙️ Tech Stack

- **Backend:** FastAPI  
- **Scraping:** Selenium, BeautifulSoup  
- **Vector DB:** ChromaDB  
- **RAG / LLM Integration:** LangChain + OpenAI  
- **Database:** PostgreSQL + Redis  
- **Migrations:** Alembic  
- **Auth:** OAuth2  
- **Environment Management:** pipenv  

---

⚙️ Setup Instructions
---------------------

Follow these steps to get the project running locally:

### 1️⃣ Install Pipenv

bash

```
pip install pipenv

```

### 2️⃣ Install Dependencies

bash

```
pipenv install

```

This will install all required packages listed in `Pipfile`.

### 3️⃣ Configure Environment Variables

Create a `.env` file and populate it with the required values. Use `config.py` as a reference for the expected keys.

### 4️⃣ Run Alembic Migrations

bash

```
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

```

This sets up your PostgreSQL schema.

### 5️⃣ Set Up Redis with Docker (for Chat History)

Install Docker if you haven't already: https://docs.docker.com/get-docker

Then run the following commands:

bash

```
# Pull Redis image
docker pull redis

# Start Redis container in detached mode
docker compose up -d

```

To stop the container:

bash

```
docker compose down

```

To stop and remove volumes:

bash

```
docker compose down -v
```

### 6️⃣ Launch the API Server

bash

```
uvicorn main:app --reload

```

✅ Your FastAPI server is now running at:\
👉 `http://127.0.0.1:8000`

Interactive API docs:\
👉 `http://127.0.0.1:8000/docs`

🧑‍💻 Frontend (Coming Soon)
----------------------------

A React-based frontend is currently in development. It will allow users to:

-   Interact with the chat interface
-   Manage authentication and session history

Stay tuned for updates!
